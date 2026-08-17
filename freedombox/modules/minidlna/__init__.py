# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure minidlna.
"""
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import firewall
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages, install
from plinth.utils import Version

from . import manifest, privileged

_description = [
    _('MiniDLNA is a simple media server software, with the aim of being '
      'fully compliant with DLNA/UPnP-AV clients. '
      'The MiniDLNA daemon serves media files '
      '(music, pictures, and video) to clients on a network. '
      'DLNA/UPnP is zero configuration protocol and is compliant '
      'with any device passing the DLNA Certification like portable '
      'media players, Smartphones, Televisions, and gaming systems ('
      'such as PS3 and Xbox 360) or applications such as totem and Kodi.')
]

SYSTEM_USER = 'minidlna'


class MiniDLNAApp(app_module.App):
    """Freedombox app managing miniDlna."""

    app_id = 'minidlna'

    _version = 6

    def __init__(self) -> None:
        """Initialize the app components."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('MiniDLNA'), icon_filename='minidlna',
                               description=_description,
                               manual_page='MiniDLNA',
                               clients=manifest.clients, tags=manifest.tags)
        self.add(info)

        menu_item = menu.Menu('menu-minidlna', name=info.name,
                              icon=info.icon_filename, tags=info.tags,
                              url_name='minidlna:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-minidlna', info.name, description=info.description,
            icon=info.icon_filename,
            configure_url=reverse_lazy('minidlna:index'), tags=info.tags,
            login_required=True)
        self.add(shortcut)

        packages = Packages('packages-minidlna', ['minidlna'])
        self.add(packages)

        firewall_minidlna = Firewall('firewall-minidlna', info.name,
                                     ports=['minidlna',
                                            'ssdp'], is_external=False)
        self.add(firewall_minidlna)

        daemon = Daemon('daemon-minidlna', 'minidlna')
        self.add(daemon)

        backup_restore = BackupRestore('backup-restore-minidlna',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if old_version == 3:
            # Version 3 of the app incorrectly declared port 8200 for firewall
            # local protection.
            firewall.remove_passthrough('ipv6', '-A', 'INPUT', '-p', 'tcp',
                                        '--dport', '8200', '-j', 'REJECT')
            firewall.remove_passthrough('ipv4', '-A', 'INPUT', '-p', 'tcp',
                                        '--dport', '8200', '-j', 'REJECT')

        if old_version and old_version <= 5:
            # Remove minidlna LDAP group and disable minidlna apache config
            from plinth.modules.apache import privileged as apache_privileged
            from plinth.modules.users import privileged as users_privileged

            users_privileged.remove_group('minidlna')
            apache_privileged.disable('minidlna-freedombox', 'config')

            # Restart app to reload firewall
            if self.is_enabled():
                self.disable()
                self.enable()

        if not old_version:
            self.enable()

    def force_upgrade(self, packages):
        """Force upgrade minidlna to resolve conffile prompt."""
        if 'minidlna' not in packages:
            return False

        # Allow upgrade from 1.3.0 (bookworm) to 1.3.3 (trixie) and beyond
        # 1.3.x.
        package = packages['minidlna']
        if Version(package['new_version']) > Version('1.4~'):
            return False

        media_dir = privileged.get_media_dir()
        install(['minidlna'], force_configuration='new')
        privileged.set_media_dir(media_dir)

        return True
