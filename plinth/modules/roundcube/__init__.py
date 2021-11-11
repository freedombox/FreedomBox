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
from plinth.utils import Version

from . import manifest

version = 1

managed_packages = ['sqlite3', 'roundcube', 'roundcube-sqlite3']

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

        packages = Packages('packages-roundcube', managed_packages)
        self.add(packages)

        firewall = Firewall('firewall-roundcube', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-roundcube', 'roundcube',
                              urls=['https://{host}/roundcube'])
        self.add(webserver)

        backup_restore = BackupRestore('backup-restore-roundcube',
                                       **manifest.backup)
        self.add(backup_restore)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'roundcube', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'roundcube', ['setup'])
    helper.call('post', app.enable)


def force_upgrade(helper, packages):
    """Force upgrade package to resolve conffile prompts."""
    if 'roundcube-core' not in packages:
        return False

    # Allow roundcube any lower version to upgrade to 1.4.*
    package = packages['roundcube-core']
    if Version(package['new_version']) > Version('1.5~'):
        return False

    helper.install(['roundcube-core'], force_configuration='new')
    actions.superuser_run('roundcube', ['setup'])
    return True
