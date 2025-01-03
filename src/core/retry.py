import asyncio
from functools import wraps
from typing import Any, Callable
import random

def async_retry(
    retries: int = 3,
    delay: int = 1,
    backoff: float = 2,
    exceptions: tuple = (Exception,)
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == retries - 1:
                        raise
                    
                    # Add jitter to avoid thundering herd
                    jitter = random.uniform(0, 0.1) * delay
                    sleep_time = (delay * (backoff ** attempt)) + jitter
                    
                    await asyncio.sleep(sleep_time)
            raise last_exception
        return wrapper
    return decorator
