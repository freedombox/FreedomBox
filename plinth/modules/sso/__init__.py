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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Plinth module to configure Single Sign On services.
"""
import base64
import datetime


from plinth import action_utils
from django.utils.translation import ugettext_lazy as _
from plinth import actions
from OpenSSL import crypto
from django.utils import timezone

version = 1

is_essential = True

depends = ['security']

title = _('Single Sign On')

managed_packages = ['libapache2-mod-auth-pubtkt', 'openssl', 'python3-openssl']


def setup(helper, old_version=None):
    """Install the required packages"""
    helper.install(managed_packages)
    helper.call('create-key-pair', actions.superuser_run,
                'auth-pubtkt', ['create-key-pair'])
    action_utils.service_restart('apache2')


def create_ticket(pkey, uid, validuntil, ip=None, tokens=None,
                  udata=None, graceperiod=None, extra_fields=None):
    """Create and return a signed mod_auth_pubtkt ticket."""
    fields = [
        'uid={}'.format(uid),
        'validuntil={}'.format(validuntil, type='d'),
        ip and 'cip={}'.format(ip),
        tokens and 'tokens={}'.format(','.join(tokens)),
        graceperiod and 'graceperiod={}'.format(graceperiod, type='d'),
        udata and 'udata={}'.format(udata),
        extra_fields and ';'.join(
            ['{k}={v}'.format(k, v) for k, v in extra_fields])
    ]
    data = ';'.join(filter(None, fields))
    signature = 'sig={}'.format(sign(pkey, data))
    return ';'.join([data, signature])


def sign(pkey, data):
    """Calculates and returns ticket's signature."""
    sig = crypto.sign(pkey, data, 'sha1')
    return base64.b64encode(sig).decode()


def generate_ticket(uid, private_key_file, tokens):
    """Generate a mod_auth_pubtkt ticket using login credentials."""
    with open(private_key_file, 'r') as fil:
        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, fil.read().encode())
    valid_until = minutes_from_now(30)
    grace_period = minutes_from_now(25)
    return create_ticket(
        pkey, uid, valid_until, tokens=tokens, graceperiod=grace_period)


def minutes_from_now(minutes):
    """Return a timestamp at the given number of minutes from now."""
    return (timezone.now() + datetime.timedelta(minutes=minutes)).timestamp()
