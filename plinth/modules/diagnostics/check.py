# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic check data type."""

from dataclasses import dataclass, field
from enum import StrEnum

from django.utils.translation import gettext

from plinth.utils import SafeFormatter


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


def translate(check: DiagnosticCheck) -> DiagnosticCheck:
    """Translate and format description using parameters."""
    description = gettext(check.description)
    if check.parameters:
        description = SafeFormatter().vformat(description, [],
                                              check.parameters)

    return DiagnosticCheck(check.check_id, description, check.result,
                           check.parameters)


def translate_checks(checks: list[DiagnosticCheck]) -> list[DiagnosticCheck]:
    """Translate and format diagnostic checks."""
    return [translate(check) for check in checks]
