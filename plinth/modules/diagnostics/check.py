# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic check data type."""

import dataclasses
from dataclasses import dataclass, field
from enum import StrEnum
import json

from django.utils.translation import gettext

from plinth.utils import SafeFormatter


class Result(StrEnum):
    """The result of a diagnostic check."""
    NOT_DONE = 'not_done'
    PASSED = 'passed'
    WARNING = 'warning'
    FAILED = 'failed'
    ERROR = 'error'


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


class CheckJSONEncoder(json.JSONEncoder):
    """Encode objects that include DiagnosticChecks."""

    def default(self, o):
        """Add class tag to DiagnosticChecks."""
        if isinstance(o, DiagnosticCheck):
            o = dataclasses.asdict(o)
            o.update({'__class__': 'DiagnosticCheck'})
            return o

        return super().default(o)


class CheckJSONDecoder(json.JSONDecoder):
    """Decode objects that include DiagnosticChecks."""

    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=CheckJSONDecoder.from_dict)

    @staticmethod
    def from_dict(data):
        """Convert tagged data to DiagnosticCheck."""
        if data.get('__class__') == 'DiagnosticCheck':
            return DiagnosticCheck(data['check_id'], data['description'],
                                   data['result'], data['parameters'])

        return data
