# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for Luanti (formally Minetest) server."""

import augeas
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Package, Packages
from plinth.utils import format_lazy

from . import manifest, privileged

_mods = [
    Package('minetest-mod-3d-armor') | Package('minetest-mod-player-3d-armor'),
    'minetest-mod-character-creator', 'minetest-mod-craftguide',
    'minetest-mod-infinite-chest', 'minetest-mod-lucky-block',
    'minetest-mod-maidroid', 'minetest-mod-mesecons',
    'minetest-mod-moreblocks', 'minetest-mod-moreores', 'minetest-mod-nether',
    'minetest-mod-pipeworks', 'minetest-mod-protector', 'minetest-mod-quartz',
    'minetest-mod-skyblock', 'minetest-mod-throwing',
    'minetest-mod-unified-inventory', 'minetest-mod-unifieddyes',
    'minetest-mod-worldedit'
]

_description = [
    format_lazy(
        _('Luanti, formally known as Minetest, is a multiplayer '
          'infinite-world block sandbox. This module enables the Luanti '
          'server to be run on this {box_name}, on the default port (30000). '
          'To connect to the server, a '
          '<a href="https://www.luanti.org/downloads/">Luanti client</a> '
          'is needed.'), box_name=_(cfg.box_name)),
]

CONFIG_FILE = '/etc/luanti/default.conf'
AUG_PATH = '/files' + CONFIG_FILE + '/.anon'


class MinetestApp(app_module.App):
    """FreedomBox app for Luanti (formally Minetest)."""

    app_id = 'minetest'

    _version = 3

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Luanti'), icon_filename='minetest',
                               description=_description,
                               manual_page='Minetest',
                               clients=manifest.clients, tags=manifest.tags,
                               donation_url='https://www.luanti.org/donate/')
        self.add(info)

        menu_item = menu.Menu('menu-minetest', info.name, info.icon_filename,
                              info.tags, 'minetest:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut(
            'shortcut-minetest', info.name, icon=info.icon_filename,
            description=info.description, manual_page=info.manual_page,
            configure_url=reverse_lazy('minetest:index'), clients=info.clients,
            tags=info.tags, login_required=False)
        self.add(shortcut)

        packages = Packages('packages-minetest', ['luanti-server'] + _mods)
        self.add(packages)

        firewall = Firewall('firewall-minetest', info.name,
                            ports=['minetest-plinth'], is_external=True)
        self.add(firewall)

        daemon = Daemon('daemon-minetest', 'luanti-server',
                        listen_ports=[(30000, 'udp4')])
        self.add(daemon)

        users_and_groups = UsersAndGroups(
            'users-and-groups-minetest',
            reserved_usernames=['Debian-minetest'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-minetest',
                                       **manifest.backup)
        self.add(backup_restore)

    def setup(self, old_version) -> None:
        """Install and configure the app."""
        super().setup(old_version)
        privileged.setup()
        if not old_version:
            self.enable()

    def uninstall(self) -> None:
        """Uninstall the app."""
        super().uninstall()
        privileged.uninstall()


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Php/lens', 'Php.lns')
    aug.set('/augeas/load/Php/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug


def get_max_players(aug) -> int:
    """Return the maximum players allowed on the server at one time."""
    value = aug.get(AUG_PATH + '/max_users')
    if value:
        return int(value)

    return 15  # Default value


def is_creative_mode_enabled(aug) -> bool:
    """Return whether creative mode is enabled."""
    value = aug.get(AUG_PATH + '/creative_mode')
    return value == 'true'


def is_pvp_enabled(aug) -> bool:
    """Return whether PVP is enabled."""
    value = aug.get(AUG_PATH + '/enable_pvp')
    return value != 'false'


def is_damage_enabled(aug) -> bool:
    """Return whether damage is enabled."""
    value = aug.get(AUG_PATH + '/enable_damage')
    return value != 'false'


def get_configuration() -> dict[str, int | bool]:
    """Return the current configuration."""
    aug = load_augeas()
    conf = {
        'max_players': get_max_players(aug),
        'creative_mode': is_creative_mode_enabled(aug),
        'enable_pvp': is_pvp_enabled(aug),
        'enable_damage': is_damage_enabled(aug),
    }
    return conf
