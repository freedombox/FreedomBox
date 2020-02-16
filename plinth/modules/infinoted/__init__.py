# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for infinoted.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.firewall.components import Firewall
from plinth.utils import format_lazy
from plinth.views import AppView

from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 2

managed_services = ['infinoted']

managed_packages = ['infinoted']

_description = [
    _('infinoted is a server for Gobby, a collaborative text editor.'),
    format_lazy(
        _('To use it, <a href="https://gobby.github.io/">download Gobby</a>, '
          'desktop client and install it. Then start Gobby and select '
          '"Connect to Server" and enter your {box_name}\'s domain name.'),
        box_name=_(cfg.box_name)),
]

port_forwarding_info = [('TCP', 6523)]

app = None


class InfinotedApp(app_module.App):
    """FreedomBox app for infinoted."""

    app_id = 'infinoted'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('infinoted'), icon_filename='infinoted',
                               short_description=_('Gobby Server'),
                               description=_description,
                               manual_page='Infinoted', clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-infinoted', info.name,
                              info.short_description, info.icon_filename,
                              'infinoted:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-infinoted', info.name,
            short_description=info.short_description, icon=info.icon_filename,
            description=info.description,
            configure_url=reverse_lazy('infinoted:index'),
            clients=info.clients, login_required=False)
        self.add(shortcut)

        firewall = Firewall('firewall-infinoted', info.name,
                            ports=['infinoted-plinth'], is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-infinoted', managed_services[0],
                        listen_ports=[(6523, 'tcp4'), (6523, 'tcp6')])
        self.add(daemon)


def init():
    """Initialize the infinoted module."""
    global app
    app = InfinotedApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)


class InfinotedAppView(AppView):
    app_id = 'infinoted'
    port_forwarding_info = port_forwarding_info


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'infinoted', ['setup'])
    helper.call('post', app.enable)
