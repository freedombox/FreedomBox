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
Plinth module to configure PageKite
"""

from gettext import gettext as _
from plinth import cfg
from plinth.signals import domain_added

from . import utils

__all__ = ['init']

depends = ['plinth.modules.apps', 'plinth.modules.names']


def init():
    """Intialize the PageKite module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Public Visibility (PageKite)'),
                     'glyphicon-flag', 'pagekite:index', 800)

    # Register kite name with Name Services module.
    try:
        kite_name = utils.get_kite_details()['kite_name']
        enabled = utils.get_pagekite_config()['enabled']
    except IndexError:
        # no data from 'pagekite get-kite'
        kite_name = None
        enabled_services = None
    else:
        if enabled and kite_name:
            services = utils.get_pagekite_services()[0]
            enabled_services = []
            for service in services:
                if services[service]:
                    enabled_services.append(service)
        else:
            kite_name = None
            enabled_services = None

    domain_added.send_robust(sender='pagekite', domain_type='pagekite',
                             name=kite_name, description=_('Pagekite'),
                             services=enabled_services)
