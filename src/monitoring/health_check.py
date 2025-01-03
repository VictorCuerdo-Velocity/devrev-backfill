from typing import Dict, Any, Optional
from datetime import datetime
import requests
from core.logging import ContextLogger
from config import Config

class ServiceHealth:
    def __init__(self, config: Config, logger: Optional[ContextLogger] = None):
        self.config = config
        self.logger = logger or ContextLogger(__name__)
        self.last_check: Optional[datetime] = None
        self.status: Dict[str, Any] = {}

    def check_devrev_api(self) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.config.devrev_base_url.rstrip('/')}/health",
                headers={"Authorization": f"Bearer {self.config.devrev_api_token}"},
                timeout=5
            )
            response.raise_for_status()
            return {"status": "healthy", "latency_ms": response.elapsed.total_seconds() * 1000}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_snowflake(self) -> Dict[str, Any]:
        try:
            from snowflake.connector import connect
            conn = connect(
                account=self.config.snowflake_account,
                user=self.config.snowflake_user,
                password=self.config.snowflake_password,
                warehouse=self.config.snowflake_warehouse,
                database=self.config.snowflake_database,
                schema=self.config.snowflake_schema
            )
            with conn.cursor() as cursor:
                cursor.execute("SELECT CURRENT_TIMESTAMP()")
                result = cursor.fetchone()
            conn.close()
            return {"status": "healthy", "timestamp": str(result[0])}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_rate_limits(self) -> Dict[str, Any]:
        try:
            response = requests.get(
                f"{self.config.devrev_base_url.rstrip('/')}/rate_limit",
                headers={"Authorization": f"Bearer {self.config.devrev_api_token}"},
                timeout=5
            )
            response.raise_for_status()
            return {
                "status": "healthy",
                "remaining": response.headers.get("X-RateLimit-Remaining", "unknown"),
                "reset": response.headers.get("X-RateLimit-Reset", "unknown")
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_all(self) -> Dict[str, Any]:
        self.last_check = datetime.utcnow()
        self.status = {
            "timestamp": self.last_check.isoformat(),
            "services": {
                "devrev_api": self.check_devrev_api(),
                "snowflake": self.check_snowflake(),
                "rate_limits": self.check_rate_limits()
            }
        }
        
        # Calculate overall health
        self.status["overall"] = all(
            service["status"] == "healthy" 
            for service in self.status["services"].values()
        )
        
        self.logger.info(
            "Health check completed",
            status=self.status
        )
        
        return self.status

    def get_last_check(self) -> Optional[Dict[str, Any]]:
        return self.status if self.last_check else None