# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for Diagnostics app functions."""

from collections import OrderedDict
from unittest.mock import patch

from plinth.app import App, Info
from plinth.modules.diagnostics import get_results


class AppTest(App):
    """Sample App for testing."""
    app_id = 'test-app'

    def __init__(self):
        super().__init__()
        info = Info('test-app', 1)
        self.add(info)


def test_get_results():
    """Test getting the diagnostics results."""
    var = 'plinth.modules.diagnostics.current_results'
    with patch(var, {}):
        assert get_results() == {'progress_percentage': 100, 'results': {}}

    with patch(var, {
            'apps': [],
            'results': OrderedDict(),
            'progress_percentage': 0
    }):
        assert get_results() == {
            'apps': [],
            'results': {},
            'progress_percentage': 0
        }

    _ = AppTest()
    results = OrderedDict({
        'test-app': {
            'id': 'test-app',
            'diagnosis': [],
            'exception': None,
            'show_rerun_setup': False
        }
    })
    with patch(
            var, {
                'apps': [('test-app', AppTest)],
                'results': results,
                'progress_percentage': 0
            }):
        results['test-app'].update({'name': 'test-app'})
        assert get_results() == {
            'apps': [('test-app', AppTest)],
            'results': results,
            'progress_percentage': 0
        }
