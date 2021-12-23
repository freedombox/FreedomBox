# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Roundcube.
"""

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages

from . import manifest

_description = [
    _('Roundcube webmail is a browser-based multilingual IMAP '
      'client with an application-like user interface. It provides '
      'full functionality you expect from an email client, including '
      'MIME support, address book, folder manipulation, message '
      'searching and spell checking.'),
    _('You can use it by providing the username and password of the email '
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

app = None


class RoundcubeApp(app_module.App):
    """FreedomBox app for Roundcube."""

    app_id = 'roundcube'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Roundcube'), icon_filename='roundcube',
                               short_description=_('Email Client'),
                               description=_description,
                               manual_page='Roundcube',
                               clients=manifest.clients)
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

        packages = Packages(
            'packages-roundcube',
            ['sqlite3', 'roundcube', 'roundcube-core', 'roundcube-sqlite3'])
        self.add(packages)

        firewall = Firewall('firewall-roundcube', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-roundcube', 'roundcube')
        self.add(webserver)

        webserver = Webserver('webserver-roundcube-freedombox',
                              'roundcube-freedombox',
                              urls=['https://{host}/roundcube'])
        self.add(webserver)

        backup_restore = BackupRestore('backup-restore-roundcube',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'roundcube', ['pre-install'])
    app.setup(old_version)
    helper.call('post', app.enable)


def force_upgrade(helper, packages):
    """Force upgrade package to resolve conffile prompts."""
    if 'roundcube-core' not in packages:
        return False

    # Allow roundcube any version to upgrade to any version. This is okay
    # because there will no longer be conflicting file changes.
    helper.install(['roundcube-core'], force_configuration='new')
    if app.get_component('webserver-roundcube').is_enabled():
        app.get_component('webserver-roundcube-freedombox').enable()

    return True
