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
Plinth module for configuring Tor
"""

from django.template.response import TemplateResponse
from gettext import gettext as _

import actions
import cfg
from ..lib.auth import login_required


def init():
    """Initialize the Tor module"""
    menu = cfg.main_menu.find('/apps')
    menu.add_item("Tor", "icon-eye-close", "/apps/tor", 30)


@login_required
def index(request):
    """Service the index page"""
    output, error = actions.superuser_run("tor-get-ports")
    del error  # Unused

    port_info = output.split("\n")
    tor_ports = {}
    for line in port_info:
        try:
            (key, val) = line.split()
            tor_ports[key] = val
        except ValueError:
            continue

    return TemplateResponse(request, 'tor.html',
                            {'title': _('Tor Control Panel'),
                             'tor_ports': tor_ports})
