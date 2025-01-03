from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import functools

class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        half_open_timeout: int = 30
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.half_open_timeout = half_open_timeout
        self.failures = 0
        self.state = CircuitState.CLOSED
        self.last_failure_time = None
        self.last_state_change = datetime.now()

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if not self.can_execute():
                raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self.on_success()
                return result
            except Exception as e:
                self.on_failure()
                raise e
                
        return wrapper

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
            
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_state_change > timedelta(seconds=self.reset_timeout):
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = datetime.now()
                return True
            return False
            
        # HALF_OPEN state
        return True

    def on_success(self) -> None:
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failures = 0
            self.last_state_change = datetime.now()

    def on_failure(self) -> None:
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = datetime.now()