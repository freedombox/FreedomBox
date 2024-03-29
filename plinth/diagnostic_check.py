# SPDX-License-Identifier: AGPL-3.0-or-later
"""Diagnostic check data type."""

import dataclasses
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeAlias

from django.utils.translation import gettext

from plinth.utils import SafeFormatter

DiagnosticCheckParameters: TypeAlias = dict[str, str | int | bool | None]


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
    parameters: DiagnosticCheckParameters = field(default_factory=dict)

    @property
    def translated_description(self):
        """Return translated string for description."""
        description = gettext(self.description)
        if self.parameters:
            return SafeFormatter().vformat(description, [], self.parameters)

        return description


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
