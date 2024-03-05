# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure name services.
"""

import logging

from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, menu
from plinth.modules.backups.components import BackupRestore
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import components, manifest

logger = logging.getLogger(__name__)

_description = [
    format_lazy(
        _('Name Services provides an overview of the ways {box_name} can be '
          'reached from the public Internet: domain name, Tor onion service, '
          'and Pagekite. For each type of name, it is shown whether the HTTP, '
          'HTTPS, and SSH services are enabled or disabled for incoming '
          'connections through the given name.'), box_name=(cfg.box_name))
]


class NamesApp(app_module.App):
    """FreedomBox app for names."""

    app_id = 'names'

    _version = 1

    can_be_disabled = False

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True, name=_('Name Services'),
                               icon='fa-tags', description=_description,
                               manual_page='NameServices')
        self.add(info)

        menu_item = menu.Menu('menu-names', info.name, None, info.icon,
                              'names:index', parent_url_name='system')
        self.add(menu_item)

        backup_restore = BackupRestore('backup-restore-names',
                                       **manifest.backup)
        self.add(backup_restore)

    @staticmethod
    def post_init():
        """Perform post initialization operations."""
        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()


def on_domain_added(sender, domain_type, name='', description='',
                    services=None, **kwargs):
    """Add domain to global list."""
    if not domain_type:
        return

    if not name:
        return
    if not services:
        services = []

    components.DomainName('domain-' + sender + '-' + name, name, domain_type,
                          services)
    logger.info('Added domain %s of type %s with services %s', name,
                domain_type, str(services))


def on_domain_removed(sender, domain_type, name='', **kwargs):
    """Remove domain from global list."""
    if name:
        component_id = 'domain-' + sender + '-' + name
        components.DomainName.get(component_id).remove()
        logger.info('Removed domain %s of type %s', name, domain_type)
    else:
        for domain_name in components.DomainName.list():
            if domain_name.domain_type.component_id == domain_type:
                domain_name.remove()

                logger.info('Remove domain %s of type %s', domain_name.name,
                            domain_type)


######################################################
# Domain utilities meant to be used by other modules #
######################################################


def get_available_tls_domains():
    """Return an iterator with all domains able to have a certificate."""
    return (domain.name for domain in components.DomainName.list()
            if domain.domain_type.can_have_certificate)
