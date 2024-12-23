# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app to configure PageKite."""

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.names.components import DomainType
from plinth.package import Packages
from plinth.privileged import service as service_privileged
from plinth.utils import format_lazy

from . import manifest, utils

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


class PagekiteApp(app_module.App):
    """FreedomBox app for Pagekite."""

    app_id = 'pagekite'

    DAEMON = 'pagekite'

    _version = 2

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(
            app_id=self.app_id, version=self._version, depends=['names'],
            name=_('PageKite'), icon='fa-flag', description=_description,
            manual_page='PageKite', tags=manifest.tags,
            donation_url='https://pagekite.net/support/faq/#donate')
        self.add(info)

        menu_item = menu.Menu('menu-pagekite', info.name,
                              info.short_description, info.icon,
                              'pagekite:index',
                              parent_url_name='system:visibility', order=40)
        self.add(menu_item)

        packages = Packages('packages-pagekite', ['pagekite'])
        self.add(packages)

        domain_type = DomainType('domain-type-pagekite', _('PageKite Domain'),
                                 'pagekite:index', can_have_certificate=True)
        self.add(domain_type)

        daemon = Daemon('daemon-pagekite', self.DAEMON)
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-pagekite',
                                       **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        # Register kite name with Name Services module.
        if not self.needs_setup() and self.is_enabled():
            utils.update_names_module(is_enabled=True)

    def enable(self):
        """Send domain signals after enabling the app."""
        super().enable()
        utils.update_names_module(is_enabled=True)

    def disable(self):
        """Send domain signals before disabling the app."""
        utils.update_names_module(is_enabled=False)
        super().disable()

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        if not old_version:
            self.enable()

        if old_version == 1:
            service_privileged.try_restart(PagekiteApp.DAEMON)
