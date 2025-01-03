import queue
from typing import Callable, Any
from contextlib import contextmanager

class ConnectionPool:
    def __init__(
        self,
        create_connection: Callable[[], Any],
        max_size: int = 10,
        timeout: int = 30
    ):
        self.create_connection = create_connection
        self.max_size = max_size
        self.timeout = timeout
        self.pool = queue.Queue(maxsize=max_size)
        self.size = 0

    def _create_connection(self) -> Any:
        if self.size >= self.max_size:
            raise Exception("Connection pool is full")
        
        conn = self.create_connection()
        self.size += 1
        return conn

    @contextmanager
    def get_connection(self):
        try:
            connection = self.pool.get(timeout=self.timeout)
        except queue.Empty:
            connection = self._create_connection()

        try:
            yield connection
        finally:
            self.pool.put(connection)