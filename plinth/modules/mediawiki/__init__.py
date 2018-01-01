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
Plinth module to configure mediawiki.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, frontpage
from plinth.menu import main_menu

from .manifest import clients

version = 1

managed_services = ['mediawiki']

managed_packages = ['mediawiki', 'imagemagick', 'php-sqlite3']

name = 'MediaWiki'

short_description = _('Wiki Engine')

description = [
    _('MediaWiki is the wiki engine that powers Wikipedia and other WikiMedia \
    projects. A wiki engine is a program for creating a collaboratively \
    edited website. You can use MediaWiki to host a wiki-like website, take \
    notes or collaborate with friends on projects.'),
    _('This MediaWiki instance comes with a randomly generated administrator \
    password. You can set a new password in the Configuration section and  \
    login using the "admin" account. You can then create more user accounts \
    from MediaWiki itself by going to the <a href="/mediawiki/index.php/\
    Special:CreateAccount">Special:CreateAccount</a> page'),
    _('Anyone with access this Wiki can read it. Only users that are logged in \
    can make changes to the content.')
]

service = None

clients = clients


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'glyphicon-edit', 'mediawiki:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'http', 'https'
        ], is_external=True, is_enabled=is_enabled, enable=enable,
                                         disable=disable,
                                         is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('setup', actions.superuser_run, 'mediawiki', ['setup'])
    helper.call('enable', actions.superuser_run, 'mediawiki', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            name,
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running,
            ports=['http', 'https'],
        )
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    """Helper method to add a shortcut to the frontpage."""
    frontpage.add_shortcut('mediawiki', name,
                           short_description=short_description,
                           url='/mediawiki', login_required=True)


def is_running():
    """Return whether the service is running."""
    return action_utils.webserver_is_enabled('mediawiki')


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.webserver_is_enabled('mediawiki'))


def enable():
    """Enable the module."""
    actions.superuser_run('mediawiki', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('mediawiki', ['disable'])
    frontpage.remove_shortcut('mediawiki')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/mediawiki',
                                         check_certificate=False))

    return results
