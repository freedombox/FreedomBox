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
Plinth module to configure ikiwiki
"""

from django.utils.translation import ugettext_lazy as _
from plinth.utils import format_lazy

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.client import web_client
from plinth.modules.users import create_group, register_group


version = 1

managed_packages = ['ikiwiki', 'libdigest-sha-perl', 'libxml-writer-perl',
                    'xapian-omega', 'libsearch-xapian-perl',
                    'libimage-magick-perl']

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
          'group can <i>edit</i> existing ones. In the <a href="/plinth/sys/'
          'users">User Configuration</a> you can change these '
          'permissions or add new users.'), box_name=_(cfg.box_name))
]

web_clients = [web_client(name='ikiwiki', url='/ikiwiki')]

group = ('wiki', _('View and edit wiki applications'))


def init():
    """Initialize the ikiwiki module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-edit', 'ikiwiki:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'ikiwiki', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            add_shortcuts()
            register_group(group)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'ikiwiki', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            'ikiwiki', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcuts)
    create_group(group[0])


def add_shortcuts():
    sites = actions.run('ikiwiki', ['get-sites']).split('\n')
    sites = [name for name in sites if name != '']
    for site in sites:
        frontpage.add_shortcut(
            'ikiwiki_' + site, site, url='/ikiwiki/' + site,
            login_required=False, icon='ikiwiki')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('ikiwiki-plinth')


def enable():
    """Enable the module."""
    actions.superuser_run('ikiwiki', ['enable'])
    add_shortcuts()


def disable():
    """Enable the module."""
    actions.superuser_run('ikiwiki', ['disable'])
    frontpage.remove_shortcut('ikiwiki*')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/ikiwiki', check_certificate=False))

    return results
