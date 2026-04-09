"""Pipeline representation and management."""

from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class PipelineStatus(Enum):
    """Status of a pipeline."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class Pipeline:
    """Represents an ETL pipeline to monitor."""

    def __init__(
        self,
        name: str,
        source: str,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ):
        """Initialize a pipeline.

        Args:
            name: Unique identifier for the pipeline
            source: Source type (e.g., 'airflow', 'databricks', 'custom')
            description: Human-readable description
            tags: List of tags for categorization
        """
        self.name = name
        self.source = source
        self.description = description or ""
        self.tags = tags or []
        self.status = PipelineStatus.UNKNOWN
        self.last_check: Optional[datetime] = None
        self.metadata: Dict = {}

    def update_status(self, status: PipelineStatus) -> None:
        """Update pipeline status and timestamp.

        Args:
            status: New status for the pipeline
        """
        self.status = status
        self.last_check = datetime.utcnow()

    def add_metadata(self, key: str, value: any) -> None:
        """Add metadata to the pipeline.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def to_dict(self) -> Dict:
        """Convert pipeline to dictionary representation."""
        return {
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "tags": self.tags,
            "status": self.status.value,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"Pipeline(name='{self.name}', source='{self.source}', status={self.status.value})"
