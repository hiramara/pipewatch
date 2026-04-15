"""Evaluate all pipelines in a monitor against registered compliance rules."""
from __future__ import annotations

from typing import Dict, List

from pipewatch.core.compliance_config import ComplianceConfig
from pipewatch.core.pipeline_compliance import ComplianceViolation


class ComplianceReport:
    """Aggregated result of a compliance evaluation run."""

    def __init__(self, violations: List[ComplianceViolation]) -> None:
        self._violations = violations

    @property
    def violations(self) -> List[ComplianceViolation]:
        return list(self._violations)

    @property
    def compliant(self) -> bool:
        return len(self._violations) == 0

    def by_pipeline(self) -> Dict[str, List[ComplianceViolation]]:
        result: Dict[str, List[ComplianceViolation]] = {}
        for v in self._violations:
            result.setdefault(v.pipeline_name, []).append(v)
        return result

    def to_dicts(self) -> List[dict]:
        return [v.to_dict() for v in self._violations]


class ComplianceEvaluator:
    """Runs compliance rules against all pipelines tracked by a monitor."""

    def __init__(self, config: ComplianceConfig) -> None:
        self._config = config

    @property
    def config(self) -> ComplianceConfig:
        return self._config

    def evaluate(self, monitor) -> ComplianceReport:
        """Check every pipeline in *monitor* against all rules."""
        violations: List[ComplianceViolation] = []
        for pipeline in monitor.pipelines.values():
            for rule in self._config.rules:
                violation = rule.evaluate(pipeline)
                if violation is not None:
                    violations.append(violation)
        return ComplianceReport(violations)
