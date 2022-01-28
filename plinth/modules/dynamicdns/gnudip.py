# SPDX-License-Identifier: AGPL-3.0-or-later
"""
GnuDIP client for updating Dynamic DNS records.
"""

import hashlib
import logging
import socket

BUF_SIZE = 50
GNUDIP_PORT = 3495

logger = logging.getLogger(__name__)


def update(server, domain, username, password):
    """Update Dynamic DNS record."""
    domain = domain.removeprefix(username + '.')
    password_digest = hashlib.md5(password.encode()).hexdigest()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        logger.debug('Connecting to %s:%d', server, GNUDIP_PORT)
        s.connect((server, GNUDIP_PORT))
        salt = s.recv(BUF_SIZE).decode().strip()
        salted_digest = password_digest + '.' + salt
        final_digest = hashlib.md5(salted_digest.encode()).hexdigest()

        update_request = username + ':' + final_digest + ':' + domain + ':2\n'
        s.sendall(update_request.encode())

        response = s.recv(BUF_SIZE).decode().strip()
        result, new_ip = response.split(':')
        result = int(result)
        if result == 0:
            logger.info('GnuDIP update success: %s', new_ip)
        else:
            logger.warn('GnuDIP update error: %s', response)

        return result, new_ip
