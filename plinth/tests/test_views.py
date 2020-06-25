# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for common FreedomBox views.
"""

import pytest

from plinth.views import is_safe_url


@pytest.mark.parametrize('url', [
    '/plinth/login/',
    '/',
    'safe',
])
def test_is_safe_url_valid_url(url):
    """Test valid URLs for safe URL checks."""
    assert is_safe_url(url)


@pytest.mark.parametrize('url', [
    '',
    None,
    '\\plinth',
    '///plinth',
    'https://example.com/plinth/login/',
    'https:///plinth/login',
])
def test_is_safe_url_invalid_url(url):
    """Test invalid URLs for safe URL checks."""
    assert not is_safe_url(url)
