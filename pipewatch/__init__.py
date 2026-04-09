"""Pipewatch - A lightweight CLI for monitoring and alerting on ETL pipeline health."""

__version__ = "0.1.0"
__author__ = "Pipewatch Contributors"

from pipewatch.core.pipeline import Pipeline
from pipewatch.core.check import Check, CheckStatus

__all__ = ["Pipeline", "Check", "CheckStatus"]
