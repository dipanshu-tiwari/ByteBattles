import docker
import redis
import json
import threading
import uuid
from queue import Queue, Empty as QueueEmpty

from ..models import Language, IMAGE

from config import REDIS_HOST, REDIS_PORT, REDIS_DB
from config import MAX_PIDS, MAX_MEMCAP_GB, REDIS_RESULT_CHANNEL, WARM_QUEUE_PREFIX, SHUTDOWN_KEY
from config import CONTAINER_POOL_THRESHOLD, CONTAINER_WORKER_COUNT

from ..utils import setup_logger

class SandboxManager:

    def __init__(
        self,
        redis_host=REDIS_HOST,
        redis_port=REDIS_PORT,
        redis_db=REDIS_DB,
        pool_threshold=CONTAINER_POOL_THRESHOLD,
    ):

        self.client = docker.from_env()

        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            decode_responses=True
        )

        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(REDIS_RESULT_CHANNEL)

        self.task_queue = Queue()
        self.threads = []
        self.stop_event = threading.Event()
        self.pending_lock = threading.Lock()

        self.pool_threshold = pool_threshold
        self.log = setup_logger("sandbox", "logs/sandbox.log")

        self.pending = {}
        for lang in Language:
            self.pending[lang.value] = 0

    # =================================================
    # QUEUE HELPERS
    # =================================================

    def warm_queue(self, language: Language) -> str:
        return f"{WARM_QUEUE_PREFIX}:{language}"

    # =================================================
    # HEALTHCHECK
    # =================================================

    def healthcheck(self, container) -> bool:
        try:
            result = container.exec_run(["/bin/sh", "-lc", "true"])
            return result.exit_code == 0
        except Exception:
            return False

    # =================================================
    # COUNT WARM SANDBOXES
    # =================================================

    def count(self, language: Language) -> int:

        return self.redis.llen(
            self.warm_queue(language)
        )

    # =================================================
    # CREATE SANDBOX
    # =================================================

    def create_sandbox(self, language: Language):

        image = IMAGE[language]

        container = self.client.containers.create(
            name=f"sandbox_{language}_{uuid.uuid4().hex}",
            image=image,

            tty=True,
            detach=True,
            auto_remove=True,

            cap_drop=["ALL"],
            network_mode="none",
            security_opt=["no-new-privileges"],

            mem_limit=str(MAX_MEMCAP_GB) + "g",
            memswap_limit=str(MAX_MEMCAP_GB) + "g",

            pids_limit=MAX_PIDS,
            user="run",
        )

        # START CONTAINER
        container.start()

        # HEALTHCHECK
        if not self.healthcheck(container):

            try:
                container.remove(force=True)
            except Exception:
                pass

            raise RuntimeError("Healtcheck failed")

        container_id = container.id

        # PUSH TO WARM QUEUE
        self.redis.lpush(
            self.warm_queue(language),
            container_id
        )

        return container_id
    
    # =================================================
    # CREATOR WORKER
    # =================================================

    def creator_worker(self):
        while not self.stop_event.is_set():
            
            try:
                language = self.task_queue.get(timeout=1)
            except QueueEmpty:
                continue

            try:
                self.create_sandbox(language)
                with self.pending_lock:
                    self.pending[language] -= 1
            except Exception as e:
                self.task_queue.put(language)
                self.log.error(e)
            finally:
                self.task_queue.task_done()

    # =================================================
    # MAINTAIN POOL
    # =================================================

    def maintain_pool(self, language: Language):

        with self.pending_lock:
            deficit = self.pool_threshold - (self.count(language) + self.pending[language])
            if deficit <= 0:
                return
            
            self.pending[language] += deficit

        self.log.info(f"Maintaing pool - {language} - creating {deficit} containers")

        for _ in range(deficit):
            self.task_queue.put(language)
    
    # =================================================
    # CLEAN POOL
    # =================================================

    def clean_pool(self, language: Language):

        self.log.info(f"Cleaning pool - {language}")

        while self.count(language) > 0:

            try:
                container_id = self.redis.rpop(self.warm_queue(language))
                container = self.client.containers.get(container_id)
                container.stop(timeout=0)

            except Exception as e:
                self.log.error(e)

    # =================================================
    # MAIN
    # =================================================

    def run(self):
        try:
            # STARTING CREATOR WORKERS
            for _ in range(CONTAINER_WORKER_COUNT):
                t = threading.Thread(target=self.creator_worker)
                t.start()
                self.threads.append(t)

            # INITIAL POOL
            for language in Language:
                self.maintain_pool(language.value)

            self.log.info(f"Running...")

            while self.redis.get(SHUTDOWN_KEY) != "1":
                message = self.pubsub.get_message(timeout=1)
                if not message:
                    continue

                if message["type"] != "message":
                    continue

                data = message["data"]
                data = json.loads(data)
                language = data["language"]
                self.maintain_pool(language)

        except KeyboardInterrupt:
            pass
        finally:
            self.log.info(f"Stopping...")
            self.stop_event.set()

            for t in self.threads:
                t.join()
            for language in Language:
                self.clean_pool(language.value)
