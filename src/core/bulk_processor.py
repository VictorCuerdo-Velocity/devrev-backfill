from typing import List, Dict, Any, Callable, TypeVar, AsyncGenerator
import asyncio
from datetime import datetime

T = TypeVar('T')
R = TypeVar('R')

class BulkProcessor:
    def __init__(
        self,
        batch_size: int = 100,
        max_concurrent: int = 5,
        rate_limit_calls: int = 50,
        rate_limit_period: int = 10
    ):
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.rate_limiter = RateLimiter(rate_limit_calls, rate_limit_period)
        self.metrics = MetricsCollector()

    async def process_items(
        self,
        items: List[T],
        process_func: Callable[[T], R],
        checkpoint_handler: Optional[CheckpointHandler] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """Process items in batches with rate limiting and checkpointing"""
        start_time = datetime.now()
        total_items = len(items)
        current_batch = 0

        for i in range(0, total_items, self.batch_size):
            batch = items[i:i + self.batch_size]
            current_batch += 1
            
            # Rate limiting
            async with self.rate_limiter:
                # Concurrent processing with semaphore
                async with self.semaphore:
                    tasks = [
                        self._process_item(item, process_func)
                        for item in batch
                    ]
                    results = await asyncio.gather(*tasks)
                    
                    # Update checkpoint if handler provided
                    if checkpoint_handler:
                        await checkpoint_handler.save_checkpoint(
                            batch_num=current_batch,
                            items_processed=i + len(batch),
                            results=results
                        )
                    
                    # Yield batch results
                    yield ProcessingResult(
                        batch_number=current_batch,
                        total_batches=total_items // self.batch_size + 1,
                        items_processed=len(results),
                        successful=sum(1 for r in results if r.success),
                        failed=sum(1 for r in results if not r.success)
                    )

    async def _process_item(
        self,
        item: T,
        process_func: Callable[[T], R]
    ) -> ItemResult:
        """Process single item with error handling"""
        try:
            start = datetime.now()
            result = await process_func(item)
            duration = (datetime.now() - start).total_seconds()
            
            self.metrics.record_processing_time(duration)
            return ItemResult(
                item=item,
                result=result,
                success=True,
                duration=duration
            )
            
        except Exception as e:
            self.metrics.record_failure()
            return ItemResult(
                item=item,
                success=False,
                error=str(e)
            )
