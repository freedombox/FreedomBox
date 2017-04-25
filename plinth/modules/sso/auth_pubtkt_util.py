#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Module with utilities to generate a auth_pubtkt ticket and
sign it with the FreedomBox server's private key.
"""

import os
import stat
import base64
import datetime
from .constants import private_key_file_name, public_key_file_name

from OpenSSL import crypto
from django.utils import timezone


def create_key_pair(directory):
    """
    Create public/private key pair for signing the auth_pubtkt tickets.
    """
    private_key_file = os.path.join(directory, private_key_file_name)
    public_key_file = os.path.join(directory, public_key_file_name)

    os.mkdir(directory) if not os.path.exists(directory) else None

    if not all([
            os.path.exists(key_file)
            for key_file in [public_key_file, private_key_file]
    ]):
        pkey = crypto.PKey()
        pkey.generate_key(crypto.TYPE_RSA, 1024)

        with open(private_key_file, 'w') as priv_key_file:
            priv_key = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                              pkey).decode()
            priv_key_file.write(priv_key)

        with open(public_key_file, 'w') as pub_key_file:
            pub_key = crypto.dump_publickey(crypto.FILETYPE_PEM,
                                            pkey).decode()
            pub_key_file.write(pub_key)

        for fil in [directory, public_key_file, private_key_file]:
            os.chmod(fil, stat.S_IRWXU)


def minutes_from_now(minutes):
    return (timezone.now() + datetime.timedelta(minutes=minutes)).timestamp()


def generate_ticket(uid, private_key_file, tokens):
    """
    Generate a mod_auth_pubtkt ticket using login credentials
    """
    with open(private_key_file, 'r') as fil:
        pkey = crypto.load_privatekey(
            crypto.FILETYPE_PEM, fil.read().encode())
    valid_until = minutes_from_now(30)
    grace_period = minutes_from_now(25)
    return create_ticket(pkey, uid, valid_until,
                         tokens=tokens, graceperiod=grace_period)


def create_ticket(pkey, uid, validuntil, ip=None, tokens=(),
                  udata='', graceperiod=None, extra_fields=()):
    """
    Create and return a signed mod_auth_pubtkt ticket
    """
    v = 'uid=%s;validuntil=%d' % (uid, validuntil)
    if ip:
        v += ';cip=%s' % ip
    if tokens:
        v += ';tokens=%s' % ','.join(tokens)
    if graceperiod:
        v += ';graceperiod=%d' % graceperiod
    if udata:
        v += ';udata=%s' % udata
    for k, fv in extra_fields:
        v += ';%s=%s' % (k, fv)
    v += ';sig=%s' % sign(pkey, v)
    return v


def sign(pkey, data):
    """
    Calculates and returns ticket's signature.
    """
    sig = crypto.sign(pkey, data, 'sha1')
    return base64.b64encode(sig).decode()
