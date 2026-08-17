# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for setup module.
"""

from plinth.setup import store_error_message, retrieve_error_messages


def test_store_retrieve_error_message():
    """Test storing and retrieving error messages."""
    store_error_message('error 1')
    assert retrieve_error_messages() == ['error 1']

    store_error_message('error 1')
    store_error_message('error 2')
    assert retrieve_error_messages() == ['error 1', 'error 2']

    # errors are cleared after retrieving
    assert retrieve_error_messages() == []
