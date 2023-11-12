# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic check data type."""

from dataclasses import dataclass, field
from enum import StrEnum


class Result(StrEnum):
    """The result of a diagnostic check."""
    NOT_DONE = 'not_done'
    PASSED = 'passed'
    WARNING = 'warning'
    FAILED = 'failed'
    ERROR = 'error'


# TODO: Description should not be translated until we need to display it.


@dataclass
class DiagnosticCheck:
    """A diagnostic check and optional result and parameters."""
    check_id: str
    description: str
    result: Result = Result.NOT_DONE
    parameters: dict = field(default_factory=dict)
