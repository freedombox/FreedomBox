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
from modules.auth import require
import actions
import cfg

class tor(PagePlugin):
    order = 30 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("privacy.tor")
        cfg.html_root.privacy.menu.add_item("Tor", "icon-eye-close", "/privacy/tor", 30)

    @cherrypy.expose
    @require()
    def index(self):
        output, error = actions.superuser_run("tor-get-ports")
        port_info = output.split("\n")
        ports = {}
        for line in port_info:
            try:
                (key, val) = line.split()
                ports[key] = val
            except ValueError:
                continue

        main = _("""
        <p>Tor is an anonymous communication system. You can learn more about it from the <a href="https://www.torproject.org/">Tor Project</a> website. For best protection when web surfing, the Tor Project recommends that you use the <a href="https://www.torproject.org/download/download-easy.html.en">Tor Browser Bundle</a>.</p>
        <p>A Tor SOCKS port is available on your FreedomBox on TCP port 9050.</p>
        <p>Your FreedomBox is configured as a Tor bridge with obfsproxy, so it can help circumvent censorship. If your FreedomBox is behind a router or firewall, you should make sure the following ports are open, and port-forwarded, if necessary:</p>
        """)

        main += '<table class="table table-bordered table-condensed span2">'
        for key in ports:
            main += "<tr><td>" + str(key) + "</td>"
            main += "<td>" + str(ports[key]) + "</td></tr>"
        main += "</table>"

        return self.fill_template(title=_("Tor Control Panel"), main=main)
