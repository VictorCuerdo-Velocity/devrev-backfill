from typing import Dict, Any
import aiohttp
import asyncio
from datetime import datetime

class HealthChecker:
    def __init__(self, config: Config, logger: Optional[ContextLogger] = None):
        self.config = config
        self.logger = logger or ContextLogger(__name__)
        
    async def check_all(self) -> Dict[str, Any]:
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "devrev_api": await self.check_devrev_api(),
                "rate_limits": await self.check_rate_limits()
            }
        }
        
    async def check_devrev_api(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.devrev_base_url.rstrip('/')}/health",
                    headers={"Authorization": f"Bearer {self.config.devrev_api_token}"},
                    timeout=5
                ) as response:
                    if response.status == 200:
                        return {"status": "healthy", "latency_ms": response.elapsed.total_seconds() * 1000}
            return {"status": "unhealthy", "error": "API check failed"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def check_rate_limits(self) -> Dict[str, Any]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.config.devrev_base_url.rstrip('/')}/rate_limits",
                    headers={"Authorization": f"Bearer {self.config.devrev_api_token}"},
                    timeout=5
                ) as response:
                    return {
                        "status": "healthy",
                        "remaining": response.headers.get("X-RateLimit-Remaining", "unknown"),
                        "reset": response.headers.get("X-RateLimit-Reset", "unknown")
                    }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}