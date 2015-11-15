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
Plinth module for name services
"""

from django.template.response import TemplateResponse
from gettext import gettext as _

from plinth.actions import ActionError
from plinth.modules import names
from plinth.modules.firewall import firewall
from plinth.modules import pagekite
from plinth.modules.tor import tor

SERVICES = [
    ('http', _('HTTP'), 80),
    ('https', _('HTTPS'), 443),
    ('ssh', _('SSH'), 22),
]


def index(request):
    """Serve name services page."""
    status = get_status()

    return TemplateResponse(request, 'names.html',
                            {'title': _('Name Services'),
                             'status': status})


def get_status():
    """Get configured services per name."""
    domainname = names.get_domain('domainname')
    if domainname:
        try:
            external_enabled_services = firewall.get_enabled_services(
                zone='external')
            domainname_services = [service[0] in external_enabled_services
                                   for service in SERVICES]
        except ActionError:
            # This happens when firewalld is not installed.
            # TODO: Are these services actually enabled?
            domainname_services = [True for service in SERVICES]
    else:
        domainname = _('Not Available')
        domainname_services = [False for service in SERVICES]

    pagekite_name = names.get_domain('pagekite')
    if pagekite_name:
        pagekite_status = [False for service in SERVICES]
        try:
            pagekite_config = pagekite.utils.get_pagekite_config()
        except IndexError:
            # no data from 'pagekite get-kite'
            pass
        else:
            pagekite_services = pagekite.utils.get_pagekite_services()[0]
            if pagekite_config['enabled']:
                pagekite_status = [pagekite_services[service[0]]
                                   for service in SERVICES]
            else:
                pagekite_name = _('Not Available')
                pagekite_status = [False for service in SERVICES]
    else:
        pagekite_name = _('Not Available')
        pagekite_status = [False for service in SERVICES]

    tor_status = tor.get_status()
    if (tor_status['enabled'] and tor_status['is_running'] and \
        tor_status['hs_enabled']):
        hs_name = names.get_domain('hiddenservice')
        hs_status = [str(service[2]) in tor_status['hs_ports']
                     for service in SERVICES]
    else:
        hs_name = _('Not Available')
        hs_status = [False for service in SERVICES]

    status = {
        'services': [service[1] for service in SERVICES],
        'name_services': [
            {
                'type': _('Domain Name'),
                'name': domainname,
                'services_enabled': domainname_services,
            },
            {
                'type': _('Pagekite'),
                'name': pagekite_name,
                'services_enabled': pagekite_status,
            },
            {
                'type': _('Tor Hidden Service'),
                'name': hs_name,
                'services_enabled': hs_status,
            },
        ],
    }
    return status
