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

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_packages = ['sqlite3', 'roundcube', 'roundcube-sqlite3']

_description = [
    _('Roundcube webmail is a browser-based multilingual IMAP '
      'client with an application-like user interface. It provides '
      'full functionality you expect from an email client, including '
      'MIME support, address book, folder manipulation, message '
      'searching and spell checking.'),
    _('You can access Roundcube from <a href="/roundcube" data-turbolinks='
      '"false">/roundcube</a>. Provide the username and password of the email '
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

manual_page = 'Roundcube'

app = None


class RoundcubeApp(app_module.App):
    """FreedomBox app for Roundcube."""

    app_id = 'roundcube'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('Roundcube'), icon_filename='roundcube',
                               short_description=_('Email Client'),
                               description=_description,
                               manual_page='Roundcube', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-roundcube', info.name,
                              info.short_description, info.icon_filename,
                              'roundcube:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-roundcube', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/roundcube/', clients=info.clients,
                                      login_required=True)
        self.add(shortcut)

        firewall = Firewall('firewall-roundcube', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-roundcube', 'roundcube',
                              urls=['https://{host}/roundcube'])
        self.add(webserver)


def init():
    """Initialize the module."""
    global app
    app = RoundcubeApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'roundcube', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'roundcube', ['setup'])
    helper.call('post', app.enable)
