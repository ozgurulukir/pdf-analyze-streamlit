"""Health check utilities for monitoring application status."""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from app.core.config import AppConfig
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check operation."""

    component: str
    status: str  # "healthy", "degraded", "unhealthy"
    message: str = ""
    response_time_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_healthy(self) -> bool:
        """Check if the component is healthy."""
        return self.status == "healthy"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "status": self.status,
            "message": self.message,
            "response_time_ms": self.response_time_ms,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class HealthChecker:
    """
    Health checker for monitoring application components.
    Checks database, LLM, embeddings, and file system status.
    """

    def __init__(self):
        """Initialize the health checker."""
        self.config = AppConfig()
        self._checks: Dict[str, callable] = {}

    def check_database(self) -> HealthCheckResult:
        """
        Check database connectivity and integrity.

        Returns:
            HealthCheckResult: Database health status
        """
        start_time = time.time()

        try:
            from app.core.database import DatabaseManager

            db = DatabaseManager()
            # Simple query to test connection
            workspaces = db.get_workspaces()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="database",
                status="healthy",
                message="Database connection successful",
                response_time_ms=response_time,
                details={
                    "workspace_count": len(workspaces),
                    "db_path": self.config.DB_PATH,
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Database health check failed: {e}")
            return HealthCheckResult(
                component="database",
                status="unhealthy",
                message=f"Database connection failed: {str(e)}",
                response_time_ms=response_time,
            )

    def check_ollama(self) -> HealthCheckResult:
        """
        Check Ollama API connectivity.

        Returns:
            HealthCheckResult: Ollama health status
        """
        start_time = time.time()

        try:
            response = requests.get(
                f"{self.config.OLLAMA_BASE_URL}/api/tags", timeout=5
            )
            response_time = (time.time() - start_time) * 1000

            if response.status_code == 200:
                models = response.json().get("models", [])
                return HealthCheckResult(
                    component="ollama",
                    status="healthy",
                    message="Ollama connection successful",
                    response_time_ms=response_time,
                    details={
                        "available_models": len(models),
                        "base_url": self.config.OLLAMA_BASE_URL,
                    },
                )
            else:
                return HealthCheckResult(
                    component="ollama",
                    status="degraded",
                    message=f"Ollama returned status {response.status_code}",
                    response_time_ms=response_time,
                )
        except requests.exceptions.ConnectionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="ollama",
                status="unhealthy",
                message="Cannot connect to Ollama. Is it running?",
                response_time_ms=response_time,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"Ollama health check failed: {e}")
            return HealthCheckResult(
                component="ollama",
                status="unhealthy",
                message=str(e),
                response_time_ms=response_time,
            )

    def check_chroma(self) -> HealthCheckResult:
        """
        Check ChromaDB connectivity and status.

        Returns:
            HealthCheckResult: ChromaDB health status
        """
        start_time = time.time()

        try:
            from app.core.chroma import ChromaManager

            chroma = ChromaManager()
            collections = chroma.get_collections()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="chroma",
                status="healthy",
                message="ChromaDB connection successful",
                response_time_ms=response_time,
                details={
                    "collection_count": len(collections),
                    "persist_directory": self.config.CHROMA_PERSIST_DIR,
                },
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"ChromaDB health check failed: {e}")
            return HealthCheckResult(
                component="chroma",
                status="unhealthy",
                message=f"ChromaDB connection failed: {str(e)}",
                response_time_ms=response_time,
            )

    def check_file_system(self) -> HealthCheckResult:
        """
        Check file system accessibility.

        Returns:
            HealthCheckResult: File system health status
        """
        import os
        from pathlib import Path

        start_time = time.time()

        try:
            # Check data directory
            data_dir = Path(self.config.DATA_DIR)
            data_dir.mkdir(parents=True, exist_ok=True)

            # Check chroma directory
            chroma_dir = Path(self.config.CHROMA_PERSIST_DIR)
            chroma_dir.mkdir(parents=True, exist_ok=True)

            # Check if directories are writable
            test_file = data_dir / ".health_check_test"
            test_file.write_text("test")
            test_file.unlink()

            response_time = (time.time() - start_time) * 1000

            return HealthCheckResult(
                component="file_system",
                status="healthy",
                message="File system accessible",
                response_time_ms=response_time,
                details={
                    "data_dir": str(data_dir),
                    "chroma_dir": str(chroma_dir),
                    "writable": True,
                },
            )
        except PermissionError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheckResult(
                component="file_system",
                status="unhealthy",
                message="Permission denied: Cannot write to data directory",
                response_time_ms=response_time,
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            logger.error(f"File system health check failed: {e}")
            return HealthCheckResult(
                component="file_system",
                status="unhealthy",
                message=str(e),
                response_time_ms=response_time,
            )

    def check_all(self) -> Dict[str, HealthCheckResult]:
        """
        Run all health checks.

        Returns:
            Dict mapping component names to their health results
        """
        logger.info("Running all health checks")

        results = {
            "database": self.check_database(),
            "ollama": self.check_ollama(),
            "chroma": self.check_chroma(),
            "file_system": self.check_file_system(),
        }

        # Determine overall status
        healthy_count = sum(1 for r in results.values() if r.is_healthy())
        total_count = len(results)

        logger.info(f"Health checks complete: {healthy_count}/{total_count} healthy")

        return results

    def get_overall_status(self) -> str:
        """
        Get overall application health status.

        Returns:
            "healthy", "degraded", or "unhealthy"
        """
        results = self.check_all()

        unhealthy = sum(1 for r in results.values() if r.status == "unhealthy")
        degraded = sum(1 for r in results.values() if r.status == "degraded")

        if unhealthy > 0:
            return "unhealthy"
        elif degraded > 0:
            return "degraded"
        else:
            return "healthy"


# Singleton instance
_health_checker: Optional[HealthChecker] = None


def get_health_checker() -> HealthChecker:
    """Get the singleton health checker instance."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker()
    return _health_checker
