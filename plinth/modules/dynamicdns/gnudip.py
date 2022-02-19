# SPDX-License-Identifier: AGPL-3.0-or-later
"""
GnuDIP client for updating Dynamic DNS records.
"""

import hashlib
import logging
import socket as socket_module

BUF_SIZE = 128
GNUDIP_PORT = 3495
TIMEOUT = 10

logger = logging.getLogger(__name__)


def update(server, domain, username, password):
    """Update Dynamic DNS record."""
    domain = domain.removeprefix(username + '.')
    password_digest = hashlib.md5(password.encode()).hexdigest()

    with socket_module.socket(socket_module.AF_INET,
                              socket_module.SOCK_STREAM) as socket:
        logger.debug('Connecting to %s:%d, timeout %ss', server, GNUDIP_PORT,
                     TIMEOUT)
        socket.settimeout(TIMEOUT)
        socket.connect((server, GNUDIP_PORT))
        salt = socket.recv(BUF_SIZE).decode().strip()
        salted_digest = password_digest + '.' + salt
        final_digest = hashlib.md5(salted_digest.encode()).hexdigest()

        update_request = username + ':' + final_digest + ':' + domain + ':2\n'
        socket.sendall(update_request.encode())

        response = socket.recv(BUF_SIZE).decode().strip()
        result, _, new_ip = response.partition(':')
        result = (int(result) == 0)

        new_ip = new_ip if result else None
        return result, new_ip
