#!/usr/bin/env python3
"""
This module provides a simple web caching system using Redis.
It caches pages for 10 seconds and tracks the number of times each URL is accessed.
"""

import redis
import requests
from typing import Callable
from functools import wraps


# Initialize Redis client
r = redis.Redis()


def count_access(fn: Callable) -> Callable:
    """
    Decorator that increments the count of URL accesses in Redis.
    Stores under key 'count:{url}'.
    """
    @wraps(fn)
    def wrapper(url: str) -> str:
        r.incr(f"count:{url}")
        return fn(url)
    return wrapper


def cache_result(expire: int = 10) -> Callable:
    """
    Decorator that caches the result of the function in Redis.
    The cache expires after `expire` seconds.
    """
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(url: str) -> str:
            cached = r.get(url)
            if cached:
                return cached.decode('utf-8')
            result = fn(url)
            r.setex(url, expire, result)
            return result
        return wrapper
    return decorator


@count_access
@cache_result(expire=10)
def get_page(url: str) -> str:
    """
    Fetches the HTML content of a URL and caches it for 10 seconds.
    Also tracks the number of times the URL was accessed.

    Args:
        url (str): The URL to fetch.

    Returns:
        str: The HTML content of the response.
    """
    response = requests.get(url)
    return response.text
