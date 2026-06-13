import time
import docker
import redis

from config import REDIS_DB, REDIS_JOB_LIST, REDIS_HOST, REDIS_JOB_LIST, REDIS_PORT, SHUTDOWN_KEY, WORKER_PREFIX
from .database import Database
from .executor import JudgeExecutor
from .pipeline import JudgePipeline
from .redis_queue import RedisQueues
from .storage_adapter import StorageAdapter
from .types import SubmissionResult

from ..utils import setup_logger

class JudgeWorker:
    def __init__(self, identifier):
        self.identifier = identifier
        self.local_shutdown_key = f"{WORKER_PREFIX}:{identifier}:shutdown"
        self.local_heartbeat_key = f"{WORKER_PREFIX}:{identifier}:heartbeat"
        self.current_submission_key = f"{WORKER_PREFIX}:{identifier}:submission"

        self.redis = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
        self.queues = RedisQueues(self.redis)
        self.db = Database()
        self.storage = StorageAdapter()
        self.executor = JudgeExecutor()
        self.pipeline = JudgePipeline(self.db, self.storage, self.queues, self.executor)

        self.log = setup_logger(
            f"worker-{self.identifier}",
            f"logs/worker_{self.identifier}.log"
        )
    
    def _set_submission(self, submission_id):
        self.redis.set(self.current_submission_key, submission_id)
    
    def _delete_submission(self, submission_id):
        self.redis.delete(self.current_submission_key)

    def _consume_from_list(self) -> None:
        while self.redis.get(SHUTDOWN_KEY) != "1" and self.redis.get(self.local_shutdown_key) != "1":

            self.redis.set(self.local_heartbeat_key, time.time())
            
            try:
                item = self.redis.brpop(REDIS_JOB_LIST, timeout=1)
                if item is None:
                    continue
                _, payload = item
                submission_id = int(payload)

                self.log.info(f"Processing submission with ID: {submission_id}")
                self._set_submission(submission_id)
                result = self.pipeline.process_submission(submission_id)
                self._delete_submission(submission_id)
                self.log.info(f"Processed submission with ID: {result.submission_id} - Verdict: {result.verdict.value}")
            except KeyboardInterrupt:
                self.log.info("Shutting down...")
                return
            except ValueError as e:
                self.log.error(e)
            except Exception as e:
                self.log.error(f"Processing of submission ID : {submission_id} failed with error: {e} - Attempting Retry")
                self.redis.lpush(REDIS_JOB_LIST, submission_id)
                time.sleep(1)

    def run(self) -> None:
        self.log.info("judge worker starting")
        self._consume_from_list()

        self.redis.delete(self.local_shutdown_key)
        self.redis.delete(self.local_heartbeat_key)
