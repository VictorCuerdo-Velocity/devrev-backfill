import pytest
from datetime import datetime, timedelta
from core.circuit_breaker import CircuitBreaker, CircuitState

def test_circuit_breaker():
    cb = CircuitBreaker(failure_threshold=2)
    
    @cb
    def flaky_operation():
        raise Exception("Failure")
    
    # Should fail and open after 2 failures
    with pytest.raises(Exception):
        flaky_operation()
    assert cb.state == CircuitState.CLOSED
    
    with pytest.raises(Exception):
        flaky_operation()
    assert cb.state == CircuitState.OPEN