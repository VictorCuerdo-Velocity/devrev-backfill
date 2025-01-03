from typing import List, Callable, TypeVar, Generic, Optional
from dataclasses import dataclass
from core.logging import ContextLogger

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchResult(Generic[T, R]):
    input_items: List[T]
    output_items: List[R]
    success: bool
    error: Optional[Exception] = None

class BatchProcessor(Generic[T, R]):
    def __init__(
        self,
        batch_size: int,
        max_consecutive_failures: int,
        logger: Optional[ContextLogger] = None
    ):
        self.batch_size = batch_size
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.logger = logger or ContextLogger(__name__)

    def process_batch(
        self,
        items: List[T],
        process_func: Callable[[List[T]], List[R]]
    ) -> List[BatchResult[T, R]]:
        results = []
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            try:
                processed_items = process_func(batch)
                results.append(BatchResult(
                    input_items=batch,
                    output_items=processed_items,
                    success=True
                ))
                self.consecutive_failures = 0
                
            except Exception as e:
                self.consecutive_failures += 1
                self.logger.error(
                    "Batch processing failed",
                    batch_index=i//self.batch_size,
                    error=str(e)
                )
                results.append(BatchResult(
                    input_items=batch,
                    output_items=[],
                    success=False,
                    error=e
                ))
                
                if self.consecutive_failures >= self.max_consecutive_failures:
                    raise Exception(
                        f"Max consecutive failures ({self.max_consecutive_failures}) reached"
                    )
                    
        return results