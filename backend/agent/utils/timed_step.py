import functools
import inspect
import time 
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def timed_step(name: str):
    """
    Decorator to time both sync and async methods and log duration under a step name.
    """

    def decorator(fn):
    
        @functools.wraps(fn)
        async def _async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await fn(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print("[STEP %s] took %.4fs", name, elapsed)
            return result

        @functools.wraps(fn)
        def _sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = fn(*args, **kwargs)
            elapsed = time.perf_counter() - start
            print("[STEP %s] took %.4fs", name, elapsed)
            return result

        return _async_wrapper if inspect.iscoroutinefunction(fn) else _sync_wrapper

    return decorator