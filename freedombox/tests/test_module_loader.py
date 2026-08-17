# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for module loading mechanism.
"""

from unittest.mock import mock_open, patch

from plinth import module_loader


@patch('pathlib.Path.open', mock_open(read_data='plinth.modules.apache\n'))
def test_get_module_import_path():
    """Returning the module import path."""
    import_path = module_loader.get_module_import_path('apache')
    assert import_path == 'plinth.modules.apache'
