# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for diagnostic check data type."""

import json
import pytest

from plinth.modules.diagnostics.check import (DiagnosticCheck,
                                              CheckJSONEncoder,
                                              CheckJSONDecoder, Result,
                                              translate)


def test_result():
    """Test result enum type."""
    assert Result.__members__['ERROR'].name == 'ERROR'
    assert Result.__members__['ERROR'].value == 'error'
    assert Result.NOT_DONE == 'not_done'
    assert Result.PASSED == 'passed'
    assert Result.WARNING == 'warning'
    assert Result.FAILED == 'failed'
    assert Result.ERROR == 'error'


def test_diagnostic_check():
    """Test the diagnostic check data class."""
    with pytest.raises(TypeError):
        DiagnosticCheck()

    check = DiagnosticCheck('some-check-id', 'sample check')
    assert check.check_id == 'some-check-id'
    assert check.description == 'sample check'
    assert check.result == Result.NOT_DONE
    assert not check.parameters

    check = DiagnosticCheck('some-check-id', 'sample check', Result.PASSED)
    assert check.result == Result.PASSED
    assert not check.parameters

    check = DiagnosticCheck('some-check-id', 'sample check', Result.PASSED,
                            {'key': 'value'})
    assert check.parameters['key'] == 'value'


def test_translate():
    """Test formatting the translated description."""
    check = DiagnosticCheck('some-check-id', 'sample check', Result.PASSED)
    translated = translate(check)
    assert translated.check_id == 'some-check-id'
    assert translated.description == 'sample check'
    assert translated.result == Result.PASSED
    assert not translated.parameters

    check = DiagnosticCheck('some-check-id', 'sample check {key}',
                            Result.FAILED, {'key': 'value'})
    translated = translate(check)
    assert translated.description == 'sample check value'
    assert translated.result == Result.FAILED
    assert translated.parameters == {'key': 'value'}

    check = DiagnosticCheck('some-check-id', 'sample check {missing}',
                            Result.PASSED, {'key': 'value'})
    translated = translate(check)
    assert translated.description == 'sample check ?missing?'


def test_json_encoder_decoder():
    """Test encoding and decoding as JSON."""
    check = DiagnosticCheck('some-check-id', 'sample check', Result.PASSED)
    check_json = json.dumps(check, cls=CheckJSONEncoder)
    for string in [
            '"check_id": "some-check-id"', '"description": "sample check"',
            '"result": "passed"', '"parameters": {}',
            '"__class__": "DiagnosticCheck"'
    ]:
        assert string in check_json

    decoded_check = json.loads(check_json, cls=CheckJSONDecoder)
    assert decoded_check == check
