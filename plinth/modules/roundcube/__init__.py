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
Plinth module to configure Roundcube.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg


version = 1

depends = ['apps']

title = _('Email Client (Roundcube)')

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


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-envelope', 'roundcube:index', 600)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'roundcube', ['pre-install'])
    helper.install(['sqlite3', 'roundcube', 'roundcube-sqlite3'])
    helper.call('pre', actions.superuser_run, 'roundcube', ['setup'])


def get_status():
    """Get the current status."""
    return {'enabled': is_enabled()}


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('roundcube')


def enable(should_enable):
    """Enable/disable the module."""
    sub_command = 'enable' if should_enable else 'disable'
    actions.superuser_run('roundcube', [sub_command])


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(action_utils.diagnose_url_on_all(
        'https://{host}/roundcube', extra_options=['--no-check-certificate']))

    return results
