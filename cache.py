#!/usr/bin/env python3
"""
Redis caching layer for the analytics API.
Provides a simple get/set/invalidate API plus a decorator to cache
Flask JSON view responses, backed by Redis with graceful degradation
if Redis is unreachable (falls through to live queries).
"""
import os
import json
import logging
from functools import wraps

import redis

logger = logging.getLogger(__name__)

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=0,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2,
)


def get_redis():
    return redis_client


def cache_get(key):
    try:
        raw = redis_client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"[Cache] GET failed for {key}: {e}")
        return None


def cache_set(key, value, ttl=60):
    try:
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as e:
        logger.warning(f"[Cache] SET failed for {key}: {e}")


def cache_delete_pattern(pattern):
    try:
        keys = list(redis_client.scan_iter(match=pattern))
        if keys:
            redis_client.delete(*keys)
    except Exception as e:
        logger.warning(f"[Cache] DELETE pattern failed for {pattern}: {e}")


def cached(key_prefix, ttl=60, vary_by=None):
    """Decorator that caches a Flask view's JSON response body in Redis.

    `vary_by`, if given, is a zero-arg callable whose return value is
    folded into the cache key (e.g. the caller's active dataset id) so
    responses never leak between tenants/datasets sharing an endpoint.
    """
    def decorator(fn):
        from flask import request, jsonify

        @wraps(fn)
        def wrapper(*args, **kwargs):
            variant = vary_by() if vary_by else ''
            cache_key = f"{key_prefix}:{variant}:{request.query_string.decode('utf-8')}"
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                response = jsonify(cached_value)
                response.headers['X-Cache'] = 'HIT'
                return response, 200

            result = fn(*args, **kwargs)
            try:
                body, status = result if isinstance(result, tuple) else (result, 200)
                data = body.get_json()
                if status == 200 and data is not None:
                    cache_set(cache_key, data, ttl)
                body.headers['X-Cache'] = 'MISS'
                return body, status
            except Exception as e:
                logger.warning(f"[Cache] Failed to store response for {cache_key}: {e}")
                return result

        return wrapper
    return decorator
