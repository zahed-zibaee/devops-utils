from redis import asyncio as aioredis
import asyncio

from app.core.config import settings
from app.core.logging import logger

class RedisClient:
    _redis = None
    _lock = asyncio.Lock()

    @classmethod
    async def get_redis(cls):
        async with cls._lock:
            if cls._redis is None or cls._redis.connection_pool is None:
                try:
                    if settings.REDIS_PASSWORD != '':
                       cls._redis = aioredis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        decode_responses=True
                        )
                    else:
                        cls._redis = aioredis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        decode_responses=True
                        )
                    await cls._redis.ping()
                except Exception as e:
                    logger.error(f"Error connecting to Redis: {e}")
                    cls._redis = None
            return cls._redis

    @classmethod
    async def close_redis(cls):
        async with cls._lock:
            if cls._redis is not None:
                cls._redis.close()
                await cls._redis.wait_closed()
                cls._redis = None
                  
    
async def get_cache(key: str, service: str):
    full_key = settings.PROJECT_NAME + ":" + service + ":" + key
    redis = await RedisClient.get_redis()
    if redis:
        try:
            value = await redis.get(full_key)
            if value:
                return value
        except Exception as e:
            logger.error(f"Error accessing Redis: {e}")
    return None

async def set_cache(key: str, service: str, value: str, expire: int = 60):
    full_key = settings.PROJECT_NAME + ":" + service + ":" + key
    redis = await RedisClient.get_redis()
    if redis:
        try:
            await redis.setex(name=full_key, value=value, time=expire)
        except Exception as e:
            logger.error(f"Error setting Redis cache: {e}")


async def lock(key: str, time: int) -> bool:
    full_key = settings.PROJECT_NAME + ":" + ":lock:" + key
    try:
        redis = await RedisClient.get_redis()
        acquired = await redis.set(full_key, "locked", ex=time, nx=True)
        if acquired:
            return True
        return False
    except Exception as e:
        logger.warning(f"Can not lock redis-lock: {e}")
        return False
    

async def unlock(key: str) -> None:
    full_key = settings.PROJECT_NAME + ":" + ":lock:" + key
    try:
        redis = await RedisClient.get_redis()
        await redis.delete(full_key)
    except Exception as e:
        logger.warning(f"Can not unlock redis-lock: {e}")
        
async def is_locked(key: str) -> bool:
    full_key = settings.PROJECT_NAME + ":" + ":lock:" + key
    try:
        redis = await RedisClient.get_redis()
        if await redis.exists(full_key):
            return True
        return False
    except Exception as e:
        logger.warning(f"Can not check redis-lock: {e}")
        return False
    