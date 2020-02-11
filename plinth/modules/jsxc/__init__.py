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
FreedomBox app to configure XMPP web client/jsxc.
"""

import logging

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.firewall.components import Firewall

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_packages = ['libjs-jsxc']

_description = [
    _('JSXC is a web client for XMPP. Typically it is used with an XMPP '
      'server running locally.'),
]

logger = logging.getLogger(__name__)

app = None


class JSXCApp(app_module.App):
    """FreedomBox app for JSXC."""

    app_id = 'jsxc'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('JSXC'), icon_filename='jsxc',
                               short_description=_('Chat Client'),
                               description=_description, clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-jsxc', info.name, info.short_description,
                              info.icon_filename, 'jsxc:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-jsxc', name=info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url=reverse_lazy('jsxc:jsxc'),
                                      clients=info.clients)
        self.add(shortcut)

        firewall = Firewall('firewall-jsxc', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)


def init():
    """Initialize the JSXC module"""
    global app
    app = JSXCApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
