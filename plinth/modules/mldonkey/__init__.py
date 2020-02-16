# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for mldonkey.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group
from plinth.utils import format_lazy

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

managed_services = ['mldonkey-server']

managed_packages = ['mldonkey-server']

_description = [
    _('MLDonkey is a peer-to-peer file sharing application used to exchange '
      'large files. It can participate in multiple peer-to-peer networks '
      'including eDonkey, Kademlia, Overnet, BitTorrent and DirectConnect.'),
    _('Users belonging to admin and ed2k group can control it through the web '
      'interface. Users in the admin group can also control it through any of '
      'the separate mobile or desktop front-ends or a telnet interface. See '
      'manual.'),
    format_lazy(
        _('On {box_name}, downloaded files can be found in /var/lib/mldonkey/ '
          'directory.'), box_name=cfg.box_name)
]

reserved_usernames = ['mldonkey']

group = ('ed2k', _('Download files using eDonkey applications'))

app = None


class MLDonkeyApp(app_module.App):
    """FreedomBox app for MLDonkey."""

    app_id = 'mldonkey'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(
            app_id=self.app_id, version=version, name=_('MLDonkey'),
            icon_filename='mldonkey',
            short_description=_('Peer-to-peer File Sharing'),
            description=_description, manual_page='MLDonkey', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-mldonkey', info.name,
                              info.short_description, info.icon_filename,
                              'mldonkey:index', parent_url_name='apps')
        self.add(menu_item)

        shortcuts = frontpage.Shortcut(
            'shortcut-mldonkey', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            url='/mldonkey/', login_required=True, clients=info.clients,
            allowed_groups=[group[0]])
        self.add(shortcuts)

        firewall = Firewall('firewall-mldonkey', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-mldonkey', 'mldonkey-freedombox',
                              urls=['https://{host}/mldonkey/'])
        self.add(webserver)

        daemon = Daemon('daemon-mldonkey', managed_services[0],
                        listen_ports=[(4080, 'tcp4')])
        self.add(daemon)


def init():
    """Initialize the MLDonkey module."""
    global app
    app = MLDonkeyApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'mldonkey', ['pre-install'])
    helper.install(managed_packages)
    helper.call('post', app.enable)
