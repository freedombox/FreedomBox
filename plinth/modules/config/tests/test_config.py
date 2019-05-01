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
Tests for config module.
"""

import os

from plinth import __main__ as plinth_main

from ..forms import ConfigurationForm


def test_hostname_field():
    """Test that hostname field accepts only valid hostnames."""
    valid_hostnames = [
        'a', '0a', 'a0', 'AAA', '00', '0-0', 'example-hostname', 'example',
        '012345678901234567890123456789012345678901234567890123456789012'
    ]
    invalid_hostnames = [
        '', '-', '-a', 'a-', '.a', 'a.', 'a.a', '?', 'a?a',
        '0123456789012345678901234567890123456789012345678901234567890123'
    ]

    for hostname in valid_hostnames:
        form = ConfigurationForm({
            'hostname': hostname,
            'domainname': 'example.com'
        })
        assert form.is_valid()

    for hostname in invalid_hostnames:
        form = ConfigurationForm({
            'hostname': hostname,
            'domainname': 'example.com'
        })
        assert not form.is_valid()


def test_domainname_field():
    """Test that domainname field accepts only valid domainnames."""
    valid_domainnames = [
        '', 'a', '0a', 'a0', 'AAA', '00', '0-0', 'example-hostname', 'example',
        'example.org', 'a.b.c.d', 'a-0.b-0.c-0',
        '012345678901234567890123456789012345678901234567890123456789012',
        ((('x' * 63) + '.') * 3) + 'x' * 61
    ]
    invalid_domainnames = [
        '-', '-a', 'a-', '.a', 'a.', '?', 'a?a', 'a..a', 'a.-a', '.',
        ((('x' * 63) + '.') * 3) + 'x' * 62, 'x' * 64
    ]

    for domainname in valid_domainnames:
        form = ConfigurationForm({
            'hostname': 'example',
            'domainname': domainname
        })
        assert form.is_valid()

    for domainname in invalid_domainnames:
        form = ConfigurationForm({
            'hostname': 'example',
            'domainname': domainname
        })
        assert not form.is_valid()


def test_locale_path():
    """
    Test that the 'locale' directory is in the same folder as __main__.py.
    This is required for detecting translated languages.
    """
    plinth_dir = os.path.dirname(plinth_main.__file__)
    locale_dir = os.path.join(plinth_dir, 'locale')
    assert os.path.isdir(locale_dir)
