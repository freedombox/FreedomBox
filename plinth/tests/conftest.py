# SPDX-License-Identifier: AGPL-3.0-or-later
"""
pytest configuration for all tests in the plinth/tests/ directory.
"""

import pathlib
from unittest.mock import patch

import pytest

from plinth import cfg


@pytest.fixture(name='shortcuts_file')
def fixture_shortcuts_file():
    with patch('plinth.frontpage.get_custom_shortcuts_paths') as func:

        def setter(file_name):
            path = pathlib.Path(__file__).parent / 'data' / 'shortcuts'
            path /= file_name
            func.return_value = cfg.expand_to_dot_d_paths([path])

        yield setter
