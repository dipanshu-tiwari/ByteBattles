from redis import Redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_JOB_LIST
redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def enqueue_job(submission_id: int):
    redis_client.lpush(REDIS_JOB_LIST, submission_id)