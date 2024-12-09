# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate a auth_pubtkt ticket.

Sign tickets with the FreedomBox server's private key.
"""

import base64
import datetime
import os
import pathlib

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from plinth.actions import privileged

KEYS_DIRECTORY = '/etc/apache2/auth-pubtkt-keys'


@privileged
def create_key_pair():
    """Create public/private key pair for signing the tickets."""
    keys_directory = pathlib.Path(KEYS_DIRECTORY)
    private_key_file = keys_directory / 'privkey.pem'
    public_key_file = keys_directory / 'pubkey.pem'

    keys_directory.mkdir(exist_ok=True)
    # Set explicitly in case permissions are incorrect
    keys_directory.chmod(0o750)
    if private_key_file.exists() and public_key_file.exists():
        # Set explicitly in case permissions are incorrect
        public_key_file.chmod(0o440)
        private_key_file.chmod(0o440)
        return

    private_key = rsa.generate_private_key(public_exponent=65537,
                                           key_size=4096)

    def opener(path, flags):
        return os.open(path, flags, mode=0o440)

    with open(private_key_file, 'wb', opener=opener) as file_handle:
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption())
        file_handle.write(pem)

    with open(public_key_file, 'wb', opener=opener) as file_handle:
        public_key = private_key.public_key()
        pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo)
        file_handle.write(pem)


def _create_ticket(private_key, uid, validuntil, ip=None, tokens=None,
                   udata=None, graceperiod=None, extra_fields=None):
    """Create and return a signed mod_auth_pubtkt ticket."""
    tokens = ','.join(tokens)
    fields = [
        f'uid={uid}',
        f'validuntil={int(validuntil)}',
        ip and f'cip={ip}',
        tokens and f'tokens={tokens}',
        graceperiod and f'graceperiod={int(graceperiod)}',
        udata and f'udata={udata}',
        extra_fields
        and ';'.join(['{}={}'.format(k, v) for k, v in extra_fields]),
    ]
    data = ';'.join(filter(None, fields))
    signature = 'sig={}'.format(_sign(private_key, data))
    return ';'.join([data, signature])


def _sign(private_key, data):
    """Calculate and return ticket's signature."""
    signature = private_key.sign(data.encode(), padding.PKCS1v15(),
                                 hashes.SHA512())
    return base64.b64encode(signature).decode()


@privileged
def generate_ticket(uid: str, private_key_file: str, tokens: list[str]) -> str:
    """Generate a mod_auth_pubtkt ticket using login credentials."""
    with open(private_key_file, 'rb') as fil:
        private_key = serialization.load_pem_private_key(
            fil.read(), password=None)

    valid_until = _minutes_from_now(12 * 60)
    grace_period = _minutes_from_now(11 * 60)
    return _create_ticket(private_key, uid, valid_until, tokens=tokens,
                          graceperiod=grace_period)


def _minutes_from_now(minutes):
    """Return a timestamp at the given number of minutes from now."""
    return _seconds_from_now(minutes * 60)


def _seconds_from_now(seconds):
    """Return a timestamp at the given number of seconds from now."""
    return (datetime.datetime.now() +
            datetime.timedelta(0, seconds)).timestamp()
