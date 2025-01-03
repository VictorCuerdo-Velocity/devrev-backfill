import psutil
import os
from typing import Dict, Any

class SystemDiagnostics:
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get system resource metrics"""
        process = psutil.Process(os.getpid())
        
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_percent': process.memory_percent(),
            'memory_info': process.memory_info()._asdict(),
            'num_threads': process.num_threads(),
            'connections': len(process.connections()),
            'open_files': len(process.open_files())
        }

    @staticmethod 
    def log_metrics(logger: ContextLogger) -> None:
        """Log system metrics"""
        metrics = SystemDiagnostics.get_metrics()
        logger.info(
            "System metrics",
            metrics=metrics
        )