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

import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
from ..lib.auth import require
import actions
import cfg
import util


class tor(PagePlugin):
    order = 60  # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps.tor")
        cfg.html_root.apps.menu.add_item("Tor", "icon-eye-close", "/apps/tor",
                                         30)

    @cherrypy.expose
    @require()
    def index(self):
        output, error = actions.superuser_run("tor-get-ports")
        port_info = output.split("\n")
        tor_ports = {}
        for line in port_info:
            try:
                (key, val) = line.split()
                tor_ports[key] = val
            except ValueError:
                continue

        return util.render_template(template='tor',
                                    title=_('Tor Control Panel'),
                                    tor_ports=tor_ports)
