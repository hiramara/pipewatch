"""pipewatch.core — public API surface."""
from pipewatch.core.pipeline import Pipeline, PipelineStatus
from pipewatch.core.check import Check, CheckStatus
from pipewatch.core.alert import Alert, AlertLevel
from pipewatch.core.monitor import Monitor
from pipewatch.core.reporter import Reporter
from pipewatch.core.formatter import render
from pipewatch.core.notifier import Notifier, LogChannel
from pipewatch.core.scheduler import Scheduler, SchedulerConfig
from pipewatch.core.history import PipelineHistory, RunRecord
from pipewatch.core.history_collector import HistoryCollector
from pipewatch.core.threshold import Threshold, ThresholdOperator
from pipewatch.core.threshold_evaluator import ThresholdEvaluator
from pipewatch.core.threshold_config import ThresholdConfig
from pipewatch.core.snapshot import Snapshot, PipelineSnapshot
from pipewatch.core.snapshot_manager import SnapshotManager
from pipewatch.core.tag import TagSet
from pipewatch.core.tag_filter import TagFilter
from pipewatch.core.pipeline_filter import PipelineFilter
from pipewatch.core.baseline import BaselineMetric
from pipewatch.core.baseline_manager import BaselineManager
from pipewatch.core.baseline_alert import BaselineAlerter
from pipewatch.core.dependency import DependencyGraph
from pipewatch.core.mute import MuteRule
from pipewatch.core.mute_manager import MuteManager
from pipewatch.core.mute_filter import MuteFilter
from pipewatch.core.escalation import EscalationPolicy, EscalationManager
from pipewatch.core.escalation_handler import EscalationHandler

__all__ = [
    "Pipeline", "PipelineStatus",
    "Check", "CheckStatus",
    "Alert", "AlertLevel",
    "Monitor",
    "Reporter",
    "render",
    "Notifier", "LogChannel",
    "Scheduler", "SchedulerConfig",
    "PipelineHistory", "RunRecord",
    "HistoryCollector",
    "Threshold", "ThresholdOperator",
    "ThresholdEvaluator",
    "ThresholdConfig",
    "Snapshot", "PipelineSnapshot",
    "SnapshotManager",
    "TagSet",
    "TagFilter",
    "PipelineFilter",
    "BaselineMetric",
    "BaselineManager",
    "BaselineAlerter",
    "DependencyGraph",
    "MuteRule",
    "MuteManager",
    "MuteFilter",
    "EscalationPolicy", "EscalationManager",
    "EscalationHandler",
]
