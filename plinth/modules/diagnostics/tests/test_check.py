# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for diagnostic check data type."""

import pytest

from plinth.modules.diagnostics.check import DiagnosticCheck, Result


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
    check = DiagnosticCheck('some-check-id', 'sample check', Result.PASSED)
    assert check.result == Result.PASSED
