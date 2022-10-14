# SPDX-License-Identifier: AGPL-3.0-or-later
"""Generate a auth_pubtkt ticket.

Sign tickets with the FreedomBox server's private key.
"""

import base64
import datetime
import os

from OpenSSL import crypto

from plinth.actions import privileged

KEYS_DIRECTORY = '/etc/apache2/auth-pubtkt-keys'


@privileged
def create_key_pair():
    """Create public/private key pair for signing the tickets."""
    private_key_file = os.path.join(KEYS_DIRECTORY, 'privkey.pem')
    public_key_file = os.path.join(KEYS_DIRECTORY, 'pubkey.pem')

    os.path.exists(KEYS_DIRECTORY) or os.mkdir(KEYS_DIRECTORY)

    if not all([
            os.path.exists(key_file)
            for key_file in [public_key_file, private_key_file]
    ]):
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 4096)

        with open(private_key_file, 'w', encoding='utf-8') as priv_key_file:
            priv_key = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                              pkey).decode()
            priv_key_file.write(priv_key)

        with open(public_key_file, 'w', encoding='utf-8') as pub_key_file:
            pub_key = crypto.dump_publickey(crypto.FILETYPE_PEM, pkey).decode()
            pub_key_file.write(pub_key)

        for fil in [public_key_file, private_key_file]:
            os.chmod(fil, 0o440)


def _create_ticket(pkey, uid, validuntil, ip=None, tokens=None, udata=None,
                   graceperiod=None, extra_fields=None):
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
    signature = 'sig={}'.format(_sign(pkey, data))
    return ';'.join([data, signature])


def _sign(pkey, data):
    """Calculate and return ticket's signature."""
    sig = crypto.sign(pkey, data.encode(), 'sha512')
    return base64.b64encode(sig).decode()


@privileged
def generate_ticket(uid: str, private_key_file: str, tokens: list[str]) -> str:
    """Generate a mod_auth_pubtkt ticket using login credentials."""
    with open(private_key_file, 'r', encoding='utf-8') as fil:
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, fil.read().encode())
    valid_until = _minutes_from_now(12 * 60)
    grace_period = _minutes_from_now(11 * 60)
    return _create_ticket(pkey, uid, valid_until, tokens=tokens,
                          graceperiod=grace_period)


def _minutes_from_now(minutes):
    """Return a timestamp at the given number of minutes from now."""
    return _seconds_from_now(minutes * 60)


def _seconds_from_now(seconds):
    """Return a timestamp at the given number of seconds from now."""
    return (datetime.datetime.now() +
            datetime.timedelta(0, seconds)).timestamp()
