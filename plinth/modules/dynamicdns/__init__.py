#
# This file is part of FreedomBox.
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
FreedomBox app to configure ez-ipupdate client.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions, cfg
from plinth.menu import main_menu
from plinth.modules import firewall
from plinth.modules.names import SERVICES
from plinth.signals import domain_added
from plinth.utils import format_lazy

from .manifest import backup

version = 1

managed_packages = ['ez-ipupdate']

name = _('Dynamic DNS Client')

description = [
    format_lazy(
        _('If your Internet provider changes your IP address periodically '
          '(i.e. every 24h), it may be hard for others to find you on the '
          'Internet. This will prevent others from finding services which are '
          'provided by this {box_name}.'), box_name=_(cfg.box_name)),
    _('The solution is to assign a DNS name to your IP address and '
      'update the DNS name every time your IP is changed by your '
      'Internet provider. Dynamic DNS allows you to push your current '
      'public IP address to a '
      '<a href=\'http://gnudip2.sourceforge.net/\' target=\'_blank\'> '
      'GnuDIP</a> server. Afterwards, the server will assign your DNS name '
      'to the new IP, and if someone from the Internet asks for your DNS '
      'name, they will get a response with your current IP address.')
]

reserved_usernames = ['ez-ipupd']

manual_page = 'DynamicDNS'


def init():
    """Initialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'fa-refresh', 'dynamicdns:index')
    current_status = get_status()
    if current_status['enabled']:
        services = get_enabled_services(current_status['dynamicdns_domain'])
        domain_added.send_robust(
            sender='dynamicdns', domain_type='dynamicdnsservice',
            name=current_status['dynamicdns_domain'],
            description=_('Dynamic DNS Service'), services=services)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)


def get_enabled_services(domain_name):
    """Get enabled services for the domain name."""
    if domain_name != None and domain_name != '':
        try:
            domainname_services = firewall.get_enabled_services(
                zone='external')
        except actions.ActionError:
            domainname_services = [service[0] for service in SERVICES]
    else:
        domainname_services = None
    return domainname_services


def get_status():
    """Return the current status."""
    # TODO: use key/value instead of hard coded value list
    status = {}
    output = actions.superuser_run('dynamicdns', ['status'])
    details = output.split()
    status['enabled'] = (output.split()[0] == 'enabled')

    if len(details) > 1:
        if details[1] == 'disabled':
            status['dynamicdns_server'] = ''
        else:
            status['dynamicdns_server'] = details[1].replace("'", "")
    else:
        status['dynamicdns_server'] = ''

    if len(details) > 2:
        if details[2] == 'disabled':
            status['dynamicdns_domain'] = ''
        else:
            status['dynamicdns_domain'] = details[2].replace("'", "")
    else:
        status['dynamicdns_domain'] = ''

    if len(details) > 3:
        if details[3] == 'disabled':
            status['dynamicdns_user'] = ''
        else:
            status['dynamicdns_user'] = details[3].replace("'", "")
    else:
        status['dynamicdns_user'] = ''

    if len(details) > 4:
        if details[4] == 'disabled':
            status['dynamicdns_secret'] = ''
        else:
            status['dynamicdns_secret'] = details[4].replace("'", "")
    else:
        status['dynamicdns_secret'] = ''

    if len(details) > 5:
        if details[5] == 'disabled':
            status['dynamicdns_ipurl'] = ''
        else:
            status['dynamicdns_ipurl'] = details[5].replace("'", "")
    else:
        status['dynamicdns_ipurl'] = ''

    if len(details) > 6:
        if details[6] == 'disabled':
            status['dynamicdns_update_url'] = ''
        else:
            status['dynamicdns_update_url'] = details[6].replace("'", "")
    else:
        status['dynamicdns_update_url'] = ''

    if len(details) > 7:
        status['disable_SSL_cert_check'] = (output.split()[7] == 'enabled')
    else:
        status['disable_SSL_cert_check'] = False

    if len(details) > 8:
        status['use_http_basic_auth'] = (output.split()[8] == 'enabled')
    else:
        status['use_http_basic_auth'] = False

    if not status['dynamicdns_server'] and not status['dynamicdns_update_url']:
        status['service_type'] = 'GnuDIP'
    elif not status['dynamicdns_server'] and status['dynamicdns_update_url']:
        status['service_type'] = 'other'
    else:
        status['service_type'] = 'GnuDIP'

    return status
