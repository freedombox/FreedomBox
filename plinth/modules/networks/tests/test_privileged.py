# SPDX-License-Identifier: AGPL-3.0-or-later
"""Test privileged method for networks app."""

from unittest.mock import patch

from .. import privileged


@patch('subprocess.check_output')
def test_get_interfaces(check_output):
    """Test returning list of network interfaces in sorted order."""
    check_output.return_value = '\n'.join([
        'ethernet:ve-fbx-testing',
        'ethernet:enp39s0',
        'ethernet:enp32s1',
        'ethernet:enp4s1',
        'bridge:virbr0',
        'wifi:wlp41s0',
        'loopback:lo',
    ]).encode()

    interfaces = privileged._get_interfaces()
    assert interfaces == {
        'ethernet': ['enp4s1', 'enp32s1', 'enp39s0', 've-fbx-testing'],
        'bridge': ['virbr0'],
        'wifi': ['wlp41s0'],
        'loopback': ['lo']
    }
