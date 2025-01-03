import asyncio
from datetime import datetime, timedelta
from typing import Optional

class RateLimiter:
    def __init__(
        self,
        calls: int,
        period: int,
        logger: Optional[ContextLogger] = None
    ):
        self.calls = calls
        self.period = period
        self.logger = logger or ContextLogger(__name__)
        self._call_times = []
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = datetime.now()
            
            # Remove old timestamps
            cutoff = now - timedelta(seconds=self.period)
            self._call_times = [t for t in self._call_times if t > cutoff]
            
            if len(self._call_times) >= self.calls:
                # Calculate sleep time
                oldest = min(self._call_times)
                sleep_time = (oldest + timedelta(seconds=self.period) - now).total_seconds()
                if sleep_time > 0:
                    self.logger.debug(f"Rate limit hit, sleeping for {sleep_time}s")
                    await asyncio.sleep(sleep_time)
                    
            self._call_times.append(now)

# Updated main.py error handling
async def main():
    try:
        # Initialize components
        config = Config()
        metrics = MetricsCollector() 
        health = await HealthChecker(config).check_all()
        
        if not health["services"]["devrev_api"]["status"] == "healthy":
            raise RuntimeError("DevRev API health check failed")
            
        rate_limits = health["services"]["rate_limits"]
        if int(rate_limits["remaining"]) < 100:
            raise RuntimeError("Insufficient API rate limits remaining")
            
        # Process with rate limiting
        rate_limiter = RateLimiter(calls=50, period=10)  # 50 calls per 10 seconds
        async with rate_limiter:
            result = await process_issues(...)
        
        return 0 if result.failed_updates == 0 else 1
            
    except Exception as e:
        logger.error(f"Critical error: {str(e)}", exc_info=True)
        return 1