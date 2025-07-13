import redis
import uuid
from typing import Union


class Cache:
    """
    Stores and retrieves data using Redis.
    """
    def __init__(self):
        """
        1. Initializes the Cache.
        2. Creates a Redis client.
        3. Flush the current Redis database.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store the data using a random generated key.
        Args:
            data: str, bytes, int, float
        Returns:
            Random generated key
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key
        