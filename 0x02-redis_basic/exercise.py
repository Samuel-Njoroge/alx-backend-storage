#!/usr/bin/env python3
"""
This module defines a Cache class that provides a simple
interface for interacting with Redis, including storing
data, retrieving data, counting calls, and tracking call history.
"""

import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """
    Decorator that counts how many times a method is called.
    Stores the count in Redis under the method's qualified name.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """
    Decorator that stores the history of inputs and outputs for a method.
    Saves inputs to <method_name>:inputs and outputs to <method_name>:outputs in Redis.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        input_key = f"{method.__qualname__}:inputs"
        output_key = f"{method.__qualname__}:outputs"

        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


class Cache:
    """
    Cache class for storing and retrieving data using Redis.
    Supports call counting and call history tracking.
    """

    def __init__(self):
        """
        Initialize the Cache instance with a Redis client.
        Flushes the Redis database to start fresh.
        """
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """
        Store data in Redis under a randomly generated UUID key.

        Args:
            data: The data to store (str, bytes, int, or float).

        Returns:
            The Redis key used to store the data.
        """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str, fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """
        Retrieve data from Redis by key, optionally applying a conversion function.

        Args:
            key: The Redis key to retrieve.
            fn: An optional function to convert the result.

        Returns:
            The retrieved value, possibly converted using fn, or None if key is not found.
        """
        value = self._redis.get(key)
        if value is None:
            return None
        return fn(value) if fn else value

    def get_str(self, key: str) -> Optional[str]:
        """
        Retrieve a UTF-8 string from Redis.

        Args:
            key: The Redis key.

        Returns:
            The string value or None if key is not found.
        """
        return self.get(key, fn=lambda d: d.decode('utf-8'))

    def get_int(self, key: str) -> Optional[int]:
        """
        Retrieve an integer value from Redis.

        Args:
            key: The Redis key.

        Returns:
            The integer value or None if key is not found.
        """
        return self.get(key, fn=int)


def replay(method: Callable) -> None:
    """
    Display the history of calls to a method.

    Args:
        method: The method whose history is to be displayed.
    """
    r = method.__self__._redis
    name = method.__qualname__
    inputs = r.lrange(f"{name}:inputs", 0, -1)
    outputs = r.lrange(f"{name}:outputs", 0, -1)

    print(f"{name} was called {len(inputs)} times:")
    for inp, out in zip(inputs, outputs):
        print(f"{name}(*{inp.decode('utf-8')}) -> {out.decode('utf-8')}")
