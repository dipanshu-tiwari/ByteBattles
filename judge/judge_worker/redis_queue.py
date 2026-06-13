import json
from typing import Any, Optional

import redis

from config import (
    REDIS_RESULT_CHANNEL,
    WARM_QUEUE_PREFIX,
)

from  ..models import Language, Verdict


class RedisQueues:
    def __init__(self, client: redis.Redis):
        self.r = client

    def warm_queue(self, language: Language) -> str:
        return f"{WARM_QUEUE_PREFIX}:{language}"

    def publish_event(self, payload: dict[str, Any]) -> None:
        self.r.publish(REDIS_RESULT_CHANNEL, json.dumps(payload, separators=(",", ":")))

    def acquire_warm_sandbox(self, language: Language, timeout: int = 0) -> str | None:
        result = self.r.brpop(self.warm_queue(language), timeout=timeout)
        if result is None:
            return None
        _, container_id = result
        return container_id

    def warm_count(self, language: str) -> int:
        return int(self.r.llen(self.warm_queue(language)))
