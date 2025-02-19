import uuid
import redis
from redis import Redis
from app.core.config import settings
from app.core.logging import logger

LOCK_PREFIX = f"{settings.PROJECT_NAME}:locks:"

def get_redis() -> Redis:
    """Returns a Redis client instance with connection pooling."""
    try:
        return redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
        
def get_cache(service: str, key: str):
    """Retrieve a cached value from Redis."""
    full_key = f"{settings.PROJECT_NAME}:{service}:{key}"
    redis_client = get_redis()
    
    try:
        return redis_client.get(full_key)
    except Exception as e:
        logger.error(f"Error accessing Redis cache: {e}")
        return None

def set_cache(service: str, key: str, value: str, expire: int = 60):
    """Set a cache value in Redis with an expiration time."""
    full_key = f"{settings.PROJECT_NAME}:{service}:{key}"
    redis_client = get_redis()
    
    try:
        redis_client.setex(name=full_key, value=value, time=expire)
    except Exception as e:
        logger.error(f"Error setting Redis cache: {e}")

def lock(key: str, time: int) -> str | None:
    """Acquire a Redis lock with a unique UUID token."""
    redis_client = get_redis()
    full_key = LOCK_PREFIX + key
    token = str(uuid.uuid4())

    try:
        acquired = redis_client.set(full_key, token, ex=time, nx=True)
        return token if acquired else None
    except Exception as e:
        logger.warning(f"Failed to acquire Redis lock: {e}")
        return None

def unlock(key: str, token: str) -> bool:
    """Release the lock only if the stored value matches the token (prevents race conditions)."""
    redis_client = get_redis()
    full_key = LOCK_PREFIX + key

    lua_script = """
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
    """

    try:
        return redis_client.eval(lua_script, 1, full_key, token) == 1
    except Exception as e:
        logger.warning(f"Failed to unlock Redis lock: {e}")
        return False

def is_locked(key: str) -> bool:
    """Check if the Redis lock exists."""
    redis_client = get_redis()
    full_key = LOCK_PREFIX + key

    try:
        return redis_client.exists(full_key) == 1   
    except Exception as e:
        logger.warning(f"Failed to check Redis lock: {e}")
        return False
