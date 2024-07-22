from redis import Redis

from app.core.config import settings
from app.core.logging import logger

redis = None

def get_redis() -> Redis:
    global redis
    if redis is None or redis.connection_pool is None:
        try:
            redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
        except:
            logger.error("Can not connect to redis service!")
            raise 
    return redis 

def close_redis() -> None:
    global redis
    if redis is not None:
        redis.close()
        redis = None      
   
def get_cache(key: str, service: str):
    full_key = settings.PROJECT_NAME + ":" + service + ":" + key
    redis = get_redis()
    try:
        value = redis.get(full_key)
        if value:
            return value
    except Exception as e:
        logger.error(f"Error accessing Redis: {e}")
    return None

def set_cache(key: str, service: str, value: str, expire: int = 60):
    full_key = settings.PROJECT_NAME + ":" + service + ":" + key
    redis = get_redis()
    try:
        redis.setex(name=full_key, value=value, time=expire)
    except Exception as e:
        logger.error(f"Error setting Redis cache: {e}")


def lock(key: str, time: int) -> bool:
    full_key = settings.PROJECT_NAME + ":locks:" + key
    redis = get_redis()
    try:
        acquired = redis.set(full_key, "locked", ex=time, nx=True)
        if acquired:
            return True
        return False
    except Exception as e:
        logger.warning(f"Can not lock redis-lock: {e}")
        return False
    

def unlock(key: str) -> None:
    full_key = settings.PROJECT_NAME + ":locks:" + key
    redis = get_redis()
    try:
        redis.delete(full_key)
    except Exception as e:
        logger.warning(f"Can not unlock redis-lock: {e}")
        
def is_locked(key: str) -> bool:
    full_key = settings.PROJECT_NAME + ":locks:" + key
    redis = get_redis()
    try:
        if redis.exists(full_key):
            return True
        return False
    except Exception as e:
        logger.warning(f"Can not check redis-lock: {e}")
        return False
    