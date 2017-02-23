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

from django.utils.translation import ugettext_lazy as _

from plinth import actions, action_utils, cfg, frontpage, service as service_module

version = 1

title_en = 'Federated Social Network (diaspora*)'

title = _(title_en)

depends = ['apps']

service = None

managed_services = ['diaspora']

managed_packages = ['diaspora']

description = [
    _('diaspora* is a decentralized social network where you can store and control your own data.'
      ), _('When enabled, the diaspora* pod will be available from '
           '<a href="/diaspora">/diaspora</a> path on the web server.')
]


def init():
    """Initialize the Diaspora module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-thumbs-up', 'diaspora:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'diaspora', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'diaspora', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut(
        'diaspora', title, url='/diaspora', login_required=True)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('diaspora-plinth')


def enable():
    """Enable the module."""
    actions.superuser_run('diaspora', ['enable'])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('diaspora', ['disable'])
    frontpage.remove_shortcut('diaspora')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    # results.append(action_utils.service_is_enabled('diaspora'))
    # results.append(action_utils.service_is_running('diaspora'))
    # results.append(is_enabled())
    results.extend(
        action_utils.diagnose_url_on_all(
            'https://{host}/diaspora', check_certificate=False))

    return results
