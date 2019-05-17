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
FreedomBox app to configure Roundcube.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth import service as service_module

from .manifest import backup, clients

version = 1

managed_packages = ['sqlite3', 'roundcube', 'roundcube-sqlite3']

name = _('Roundcube')

short_description = _('Email Client')

description = [
    _('Roundcube webmail is a browser-based multilingual IMAP '
      'client with an application-like user interface. It provides '
      'full functionality you expect from an email client, including '
      'MIME support, address book, folder manipulation, message '
      'searching and spell checking.'),
    _('You can access Roundcube from <a href="/roundcube">'
      '/roundcube</a>. Provide the username and password of the email '
      'account you wish to access followed by the domain name of the '
      'IMAP server for your email provider, like <code>imap.example.com'
      '</code>.  For IMAP over SSL (recommended), fill the server field '
      'like <code>imaps://imap.example.com</code>.'),
    _('For Gmail, username will be your Gmail address, password will be '
      'your Google account password and server will be '
      '<code>imaps://imap.gmail.com</code>.  Note that you will also need '
      'to enable "Less secure apps" in your Google account settings '
      '(<a href="https://www.google.com/settings/security/lesssecureapps"'
      '>https://www.google.com/settings/security/lesssecureapps</a>).'),
]

clients = clients

service = None

manual_page = 'Roundcube'

app = None


class RoundcubeApp(app_module.App):
    """FreedomBox app for Roundcube."""

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-roundcube', name, short_description,
                              'roundcube', 'roundcube:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-roundcube', name,
                                      short_description=short_description,
                                      icon='roundcube', url='/roundcube/',
                                      clients=clients, login_required=True)
        self.add(shortcut)


def init():
    """Intialize the module."""
    global app
    app = RoundcubeApp()

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            'roundcube', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)

        if is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'roundcube', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'roundcube', ['setup'])
    global service
    if service is None:
        service = service_module.Service(
            'roundcube', name, ports=['http', 'https'], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable)
    helper.call('post', app.enable)


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('roundcube')


def enable():
    """Enable the module."""
    actions.superuser_run('roundcube', ['enable'])
    app.enable()


def disable():
    """Enable the module."""
    actions.superuser_run('roundcube', ['disable'])
    app.disable()


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/roundcube',
                                         check_certificate=False))

    return results
