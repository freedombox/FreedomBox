# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Tests for wireguard module forms.
"""

import pytest
from django.core.exceptions import ValidationError

from plinth.modules.wireguard.forms import validate_endpoint, validate_key


@pytest.mark.parametrize('key', [
    'gKQhVGla4UtdqeY1dQ21G5lqrnX5NFcSEAqzM5iSdl0=',
    'uHWSYIjPnS9fYFhZ0mf22IkOMyrWXDlfpXs6ve4QGHk=',
])
def test_validate_key_valid_patterns(key):
    """Test that valid wireguard key patterns as accepted."""
    validate_key(key)


@pytest.mark.parametrize(
    'key',
    [
        # Invalid padding
        'gKQhVGla4UtdqeY1dQ21G5lqrnX5NFcSEAqzM5iSdl0',
        'invalid-base64',
        '',
        'aW52YWxpZC1sZW5ndGg=',  # Incorrect length
    ])
def test_validate_key_invalid_patterns(key):
    """Test that invalid wireguard key patterns are rejected."""
    with pytest.raises(ValidationError):
        validate_key(key)


@pytest.mark.parametrize('endpoint', [
    '[1::2]:1234',
    '1.2.3.4:1234',
    'example.com:1234',
])
def test_validate_endpoint_valid_patterns(endpoint):
    """Test that valid wireguard endpoint patterns are accepted."""
    validate_endpoint(endpoint)


@pytest.mark.parametrize(
    'endpoint',
    [
        '',
        # Invalid port
        '1.2.3.4',
        '1.2.3.4:',
        '1.2.3.4:0',
        '1.2.3.4:65536',
        '1.2.3.4:1234invalid',
        '1.2.3.4:invalid',
        # Invalid IPv6
        '[]:1234',
        '[:1234',
    ])
def test_validate_endpoint_invalid_patterns(endpoint):
    """Test that invalid wireguard endpoint patterns are rejected."""
    with pytest.raises(ValidationError):
        validate_endpoint(endpoint)
