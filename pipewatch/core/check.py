"""Health check definitions and execution."""

from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum


class CheckStatus(Enum):
    """Status of a health check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


class Check:
    """Represents a health check for a pipeline."""

    def __init__(
        self,
        name: str,
        check_type: str,
        description: Optional[str] = None,
    ):
        """Initialize a health check.

        Args:
            name: Unique name for the check
            check_type: Type of check (e.g., 'freshness', 'row_count', 'custom')
            description: Human-readable description
        """
        self.name = name
        self.check_type = check_type
        self.description = description or ""
        self.status = CheckStatus.SKIPPED
        self.executed_at: Optional[datetime] = None
        self.message: str = ""
        self.details: Dict[str, Any] = {}

    def execute(self, **kwargs) -> CheckStatus:
        """Execute the health check.

        Args:
            **kwargs: Parameters needed for the check

        Returns:
            CheckStatus indicating the result
        """
        self.executed_at = datetime.utcnow()
        # This is a base implementation - subclasses should override
        self.status = CheckStatus.SKIPPED
        self.message = "Check execution not implemented"
        return self.status

    def mark_pass(self, message: str = "", **details) -> None:
        """Mark check as passed."""
        self.status = CheckStatus.PASS
        self.message = message
        self.details = details
        self.executed_at = datetime.utcnow()

    def mark_fail(self, message: str = "", **details) -> None:
        """Mark check as failed."""
        self.status = CheckStatus.FAIL
        self.message = message
        self.details = details
        self.executed_at = datetime.utcnow()

    def mark_warning(self, message: str = "", **details) -> None:
        """Mark check as warning."""
        self.status = CheckStatus.WARNING
        self.message = message
        self.details = details
        self.executed_at = datetime.utcnow()

    @property
    def is_terminal(self) -> bool:
        """Return True if the check has been executed and reached a terminal state.

        A check is considered terminal when it has a definitive result
        (PASS, FAIL, or WARNING), as opposed to SKIPPED which indicates
        it has not yet run or was intentionally bypassed.
        """
        return self.status in (CheckStatus.PASS, CheckStatus.FAIL, CheckStatus.WARNING)

    def to_dict(self) -> Dict:
        """Convert check to dictionary representation."""
        return {
            "name": self.name,
            "check_type": self.check_type,
            "description": self.description,
            "status": self.status.value,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "message": self.message,
            "details": self.details,
        }

    def __repr__(self) -> str:
        return f"Check(name='{self.name}', type='{self.check_type}', status={self.status.value})"
