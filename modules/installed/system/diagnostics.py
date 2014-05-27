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
Plinth module for running diagnostics
"""

import cherrypy
from gettext import gettext as _
from auth import require
from plugin_mount import PagePlugin
import actions
import cfg
import util


class diagnostics(PagePlugin):
    order = 30
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.diagnostics")
        cfg.html_root.sys.menu.add_item("Diagnostics", "icon-screenshot", "/sys/diagnostics", 30)

    @cherrypy.expose
    @require()
    def index(self):
        return util.render_template(template='diagnostics',
                                    title=_('System Diagnostics'))

class test(PagePlugin):
    order = 31
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sys.diagnostics.test")

    @cherrypy.expose
    @require()
    def index(self):
        output, error = actions.superuser_run("diagnostic-test")
        return util.render_template(template='diagnostics_test',
                                    title=_('Diagnostic Test'),
                                    diagnostics_output=output,
                                    diagnostics_error=error)
