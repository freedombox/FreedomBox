# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate DKIM keys for signing outgoing messages.

See: https://rspamd.com/doc/modules/dkim_signing.html
"""

import pathlib
import re
import shutil
import subprocess

from plinth.actions import privileged

_keys_dir = pathlib.Path('/var/lib/rspamd/dkim/')

DOMAIN_PART_REGEX = r'^[a-zA-Z0-9]([-a-zA-Z0-9]{,61}[a-zA-Z0-9])?$'


def _validate_domain_name(domain):
    for part in domain.split('.'):
        if not re.match(DOMAIN_PART_REGEX, part):
            raise ValueError('Invalid domain name')


@privileged
def get_dkim_public_key(domain: str) -> str:
    """Privileged action to get the public key from DKIM key."""
    _validate_domain_name(domain)
    key_file = _keys_dir / f'{domain}.dkim.key'
    output = subprocess.check_output(
        ['openssl', 'rsa', '-in',
         str(key_file), '-pubout'], stderr=subprocess.DEVNULL)
    return ''.join(output.decode().splitlines()[1:-1])


@privileged
def setup_dkim(domain: str):
    """Create DKIM key for a given domain."""
    _validate_domain_name(domain)

    _keys_dir.mkdir(exist_ok=True)
    _keys_dir.chmod(0o500)
    shutil.chown(_keys_dir, '_rspamd', '_rspamd')

    # Default path is /var/lib/dkim/$domain.$selector.key. Default selector is
    # "dkim". Use these to simplify key management until we have a need to
    # implement creating new or multiple keys.
    key_file = _keys_dir / f'{domain}.dkim.key'
    if key_file.exists():
        return

    # Ed25519 is widely *not* accepted as of 2022-01. See:
    # https://serverfault.com/questions/1023674
    subprocess.run([
        'rspamadm', 'dkim_keygen', '-t', 'rsa', '-b', '2048', '-s', 'dkim',
        '-d', domain, '-k', (str(key_file))
    ], check=True)
    key_file.chmod(0o400)
