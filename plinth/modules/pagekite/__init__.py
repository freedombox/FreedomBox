# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure PageKite.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.names.components import DomainType
from plinth.utils import format_lazy

from . import utils
from .manifest import backup  # noqa, pylint: disable=unused-import

version = 1

depends = ['names']

managed_services = ['pagekite']

managed_packages = ['pagekite']

_description = [
    format_lazy(
        _('PageKite is a system for exposing {box_name} services when '
          'you don\'t have a direct connection to the Internet. You only '
          'need this if your {box_name} services are unreachable from '
          'the rest of the Internet. This includes the following '
          'situations:'), box_name=_(cfg.box_name)),
    format_lazy(_('{box_name} is behind a restricted firewall.'),
                box_name=_(cfg.box_name)),
    format_lazy(
        _('{box_name} is connected to a (wireless) router which you '
          'don\'t control.'), box_name=_(cfg.box_name)),
    _('Your ISP does not provide you an external IP address and '
      'instead provides Internet connection through NAT.'),
    _('Your ISP does not provide you a static IP address and your IP '
      'address changes every time you connect to Internet.'),
    _('Your ISP limits incoming connections.'),
    format_lazy(
        _('PageKite works around NAT, firewalls and IP address limitations '
          'by using a combination of tunnels and reverse proxies. You can '
          'use any pagekite service provider, for example '
          '<a href="https://pagekite.net">pagekite.net</a>.  In the future it '
          'might be possible to use your buddy\'s {box_name} for this.'),
        box_name=_(cfg.box_name))
]

app = None


class PagekiteApp(app_module.App):
    """FreedomBox app for Pagekite."""

    app_id = 'pagekite'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               depends=depends, name=_('PageKite'),
                               icon='fa-flag',
                               short_description=_('Public Visibility'),
                               description=_description,
                               manual_page='PageKite')
        self.add(info)

        menu_item = menu.Menu('menu-pagekite', info.name,
                              info.short_description, info.icon,
                              'pagekite:index', parent_url_name='system')
        self.add(menu_item)

        domain_type = DomainType('domain-type-pagekite', _('PageKite Domain'),
                                 'pagekite:index', can_have_certificate=True)
        self.add(domain_type)

        daemon = Daemon('daemon-pagekite', managed_services[0])
        self.add(daemon)


def init():
    """Initialize the PageKite module"""
    global app
    app = PagekiteApp()

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and app.is_enabled():
        app.set_enabled(True)

    # Register kite name with Name Services module.
    utils.update_names_module()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', app.enable)
