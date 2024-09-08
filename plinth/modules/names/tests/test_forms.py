# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for forms in names app."""

from ..forms import HostnameForm


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
        form = HostnameForm({'hostname': hostname})
        assert form.is_valid()

    for hostname in invalid_hostnames:
        form = HostnameForm({'hostname': hostname})
        assert not form.is_valid()
