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
FreedomBox app to configure ikiwiki.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth import service as service_module
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 1

managed_packages = [
    'ikiwiki', 'libdigest-sha-perl', 'libxml-writer-perl', 'xapian-omega',
    'libsearch-xapian-perl', 'libimage-magick-perl'
]

service = None

name = _('ikiwiki')

short_description = _('Wiki and Blog')

description = [
    _('ikiwiki is a simple wiki and blog application. It supports '
      'several lightweight markup languages, including Markdown, and '
      'common blogging functionality such as comments and RSS feeds. '
      'When enabled, the blogs and wikis will be available '
      'at <a href="/ikiwiki">/ikiwiki</a> (once created).'),
    format_lazy(
        _('Only {box_name} users in the <b>admin</b> group can <i>create</i> '
          'and <i>manage</i> blogs and wikis, but any user in the <b>wiki</b> '
          'group can <i>edit</i> existing ones. In the <a href="{users_url}">'
          'User Configuration</a> you can change these '
          'permissions or add new users.'), box_name=_(cfg.box_name),
        users_url=reverse_lazy('users:index'))
]

clients = clients

group = ('wiki', _('View and edit wiki applications'))

manual_page = 'Ikiwiki'

app = None


class IkiwikiApp(app_module.App):
    """FreedomBox app for Ikiwiki."""

    app_id = 'ikiwiki'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-ikiwiki', name, short_description,
                              'ikiwiki', 'ikiwiki:index',
                              parent_url_name='apps')
        self.add(menu_item)

        sites = actions.run('ikiwiki', ['get-sites']).split('\n')
        sites = [name for name in sites if name != '']
        for site in sites:
            self.add_shortcut(site)

        firewall = Firewall('firewall-ikiwiki', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-ikiwiki', 'ikiwiki-plinth')
        self.add(webserver)

    def add_shortcut(self, site):
        """Add an ikiwiki shortcut to frontpage."""
        shortcut = frontpage.Shortcut('shortcut-ikiwiki-' + site, site,
                                      icon='ikiwiki', url='/ikiwiki/' + site,
                                      clients=clients)
        self.add(shortcut)
        return shortcut

    def remove_shortcut(self, site):
        """Remove an ikiwiki shortcut from frontpage."""
        component = self.remove('shortcut-ikiwiki-' + site)
        component.remove()  # Remove from global list.


def init():
    """Initialize the ikiwiki module."""
    global app
    app = IkiwikiApp()
    register_group(group)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service('ikiwiki', name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)
        if is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ikiwiki', ['setup'])
    global service
    if service is None:
        service = service_module.Service('ikiwiki', name,
                                         is_enabled=is_enabled, enable=enable,
                                         disable=disable)
    helper.call('post', app.enable)


def is_enabled():
    """Return whether the module is enabled."""
    return app.is_enabled()


def enable():
    """Enable the module."""
    app.enable()


def disable():
    """Enable the module."""
    app.disable()


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/ikiwiki',
                                         check_certificate=False))

    return results
