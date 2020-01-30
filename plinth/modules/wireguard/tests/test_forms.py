#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
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
