# SPDX-License-Identifier: AGPL-3.0-or-later
"""Tests for forms in names app."""

from ..forms import DomainNameForm, HostnameForm


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


def test_domain_name_field():
    """Test that domain name field accepts only valid domain names."""
    valid_domain_names = [
        '', 'a', '0a', 'a0', 'AAA', '00', '0-0', 'example-hostname', 'example',
        'example.org', 'a.b.c.d', 'a-0.b-0.c-0',
        '012345678901234567890123456789012345678901234567890123456789012',
        ((('x' * 63) + '.') * 3) + 'x' * 61
    ]
    invalid_domain_names = [
        '-', '-a', 'a-', '.a', 'a.', '?', 'a?a', 'a..a', 'a.-a', '.',
        ((('x' * 63) + '.') * 3) + 'x' * 62, 'x' * 64
    ]

    for domain_name in valid_domain_names:
        form = DomainNameForm({'domain_name': domain_name})
        assert form.is_valid()

    for domain_name in invalid_domain_names:
        form = DomainNameForm({'domain_name': domain_name})
        assert not form.is_valid()
