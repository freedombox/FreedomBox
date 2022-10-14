# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for WireGuard."""

import subprocess

from plinth.actions import privileged

SERVER_INTERFACE = 'wg0'


@privileged
def get_info() -> dict[str, dict]:
    """Return info for each configured interface."""
    output = subprocess.check_output(['wg', 'show', 'all',
                                      'dump']).decode().strip()
    lines = output.split('\n')
    interfaces: dict[str, dict] = {}
    for line in lines:
        if not line:
            continue

        fields = [
            field if field != '(none)' else None for field in line.split()
        ]
        interface_name = fields[0]
        if interface_name in interfaces:
            latest_handshake = int(fields[5]) if int(fields[5]) else None
            peer = {
                'public_key': fields[1],
                'preshared_key': fields[2],
                'endpoint': fields[3],
                'allowed_ips': fields[4],
                'latest_handshake': latest_handshake,
                'transfer_rx': fields[6],
                'transfer_tx': fields[7],
                'persistent_keepalive': fields[8],
            }
            interfaces[interface_name]['peers'].append(peer)

        else:
            interfaces[interface_name] = {
                'interface_name': interface_name,
                'private_key': fields[1],
                'public_key': fields[2],
                'listen_port': fields[3],
                'fwmark': fields[4],
                'peers': [],
            }

    return interfaces
