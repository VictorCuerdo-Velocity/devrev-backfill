import cProfile
import pstats
import io
from functools import wraps
from typing import Callable, Any

def profile(func: Callable) -> Callable:
    """Decorator to profile function execution"""
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        print(s.getvalue())
        return result
        
    return wrapper