import time
import multiprocessing as mp
from redis import Redis

from .sandbox_manager import SandboxManager
from .judge_worker import JudgeWorker

from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_JOB_LIST, MINIMUM_JUDGE_WORKER, MAXIMUM_JUDGE_WORKER, SHUTDOWN_KEY, WORKER_PREFIX, JUDGE_WORKER_TIMEOUT

from .utils import setup_logger

class JudgeOrchestrator:
    def __init__(self):
        self.redis = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

        self.min_workers = MINIMUM_JUDGE_WORKER
        self.max_workers = MAXIMUM_JUDGE_WORKER

        self.sandbox_manager_process = None
        self.workers = []
        self.global_worker_id = 1

        self.log = setup_logger("orchestrator", "logs/orchestrator.log")

        self.redis.set(SHUTDOWN_KEY, "0")
    
    def start_sandbox_manager(self):
        self.log.info("Starting sandbox manager")

        p = mp.Process(target=SandboxManager().run)
        p.start()
        self.sandbox_manager_process = p
    
    def get_worker_id(self):
        self.global_worker_id += 1
        return self.global_worker_id - 1

    def get_queue_size(self):
        return self.redis.llen(REDIS_JOB_LIST)

    def scale(self):
        qsize = self.get_queue_size()
        current = len(self.workers)

        # simple policy
        desired = min(self.max_workers, max(self.min_workers, qsize // 5 + 1))

        if desired > current:
            for _ in range(desired - current):
                self.spawn_worker()

        elif desired < current:
            for _ in range(current - desired):
                self.stop_worker()

    def spawn_worker(self):
        identifier = self.get_worker_id()
        self.log.info(f"Spawning worker with ID: {identifier}")

        worker = JudgeWorker(identifier)
        p = mp.Process(target=worker.run)
        p.start()

        self.workers.append((identifier, p))
        self.redis.set(f"{WORKER_PREFIX}:{identifier}:shutdown", "0")
        self.redis.set(f"{WORKER_PREFIX}:{identifier}:heartbeat", time.time())

    def stop_worker(self):
        if self.workers:
            identifier, p = self.workers.pop()
            self.log.info(f"Stopping worker with ID: {identifier}")

            self.redis.set(f"{WORKER_PREFIX}:{identifier}:shutdown", "1")
            
            p.join(timeout=5)

            if p.is_alive():
                self.log.warning(f"Force killing worker {identifier}")
                p.terminate()
                p.join()
    
    def check_heartbeat(self):
        alive_workers = []
        current_time = time.time()
        for identifier, p in self.workers:
            hb = self.redis.get(f"{WORKER_PREFIX}:{identifier}:heartbeat")

            if not p.is_alive() or not hb:
                self.log.info(f"Worker was found stopped with ID: {identifier}")
                p.join()

            elif current_time - float(hb) > JUDGE_WORKER_TIMEOUT:
                self.log.info(f"Worker is frozen with ID: {identifier}")

                current_submission_id = self.redis.get(f"{WORKER_PREFIX}:{identifier}:submission")
                if current_submission_id:
                    current_submission_id = int(current_submission_id)
                    self.log.warning(f"Submission with ID: {current_submission_id} was found stuck - Attempting retry...")
                    self.redis.lpush(REDIS_JOB_LIST, current_submission_id)

                self.redis.delete(f"{WORKER_PREFIX}:{identifier}:shutdown")
                self.redis.delete(f"{WORKER_PREFIX}:{identifier}:heartbeat")
                self.redis.delete(f"{WORKER_PREFIX}:{identifier}:submission")

                p.terminate()
                p.join()

            else:
                alive_workers.append((identifier, p))
        self.workers = alive_workers

    def shutdown(self):
        self.redis.set(SHUTDOWN_KEY, "1")

        for _, p in self.workers:
            p.join()
        
        self.sandbox_manager_process.join()
        self.redis.delete(SHUTDOWN_KEY)

        self.log.info("Stoping...")

    def run(self):

        try:
            self.start_sandbox_manager()

            self.log.info("Running...")
        
            while True:
                self.check_heartbeat()
                self.scale()
                time.sleep(2)
        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.log.error(e)
            raise
        finally:
            self.shutdown()

if __name__ == "__main__":
    orchestrator = JudgeOrchestrator()
    orchestrator.run()