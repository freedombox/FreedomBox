#
# This file is part of FreedomBox.
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
FreedomBox app for Minetest server.
"""

import augeas
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions, cfg, frontpage
from plinth.menu import main_menu
from plinth.utils import format_lazy

from .manifest import backup, clients

version = 2

service = None

managed_services = ['minetest-server']

mods = [
    'minetest-mod-character-creator', 'minetest-mod-craftguide',
    'minetest-mod-infinite-chest', 'minetest-mod-lucky-block',
    'minetest-mod-maidroid', 'minetest-mod-mesecons',
    'minetest-mod-moreblocks', 'minetest-mod-moreores', 'minetest-mod-nether',
    'minetest-mod-pipeworks', 'minetest-mod-player-3d-armor',
    'minetest-mod-protector', 'minetest-mod-quartz', 'minetest-mod-skyblock',
    'minetest-mod-throwing', 'minetest-mod-torches',
    'minetest-mod-unified-inventory', 'minetest-mod-unifieddyes',
    'minetest-mod-worldedit'
]

managed_packages = ['minetest-server'] + mods

name = _('Minetest')

short_description = _('Block Sandbox')

description = [
    format_lazy(
        _('Minetest is a multiplayer infinite-world block sandbox. This '
          'module enables the Minetest server to be run on this '
          '{box_name}, on the default port (30000). To connect to the server, '
          'a <a href="http://www.minetest.net/downloads/">Minetest client</a> '
          'is needed.'), box_name=_(cfg.box_name)),
]

clients = clients

manual_page = 'Minetest'

reserved_usernames = ['Debian-minetest']

CONFIG_FILE = '/etc/minetest/minetest.conf'
AUG_PATH = '/files' + CONFIG_FILE + '/.anon'


def init():
    """Initialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(name, 'minetest', 'minetest:index', short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(managed_services[0], name, ports=[
            'minetest-plinth'
        ], is_external=True, enable=enable, disable=disable)
        if service.is_enabled():
            add_shortcut()
            menu.promote_item('minetest:index')


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(managed_services[0], name, ports=[
            'minetest-plinth'
        ], is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)
    menu = main_menu.get('apps')
    helper.call('post', menu.promote_item, 'minetest:index')


def add_shortcut():
    frontpage.add_shortcut(
        'minetest', name, url=None, short_description=short_description,
        details=description, configure_url=reverse_lazy('minetest:index'),
        login_required=False)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()
    menu = main_menu.get('apps')
    menu.promote_item('minetest:index')


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('minetest')
    menu = main_menu.get('apps')
    menu.demote_item('minetest:index')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(30000, 'udp4'))

    return results


def load_augeas():
    """Initialize Augeas."""
    aug = augeas.Augeas(
        flags=augeas.Augeas.NO_LOAD + augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Php/lens', 'Php.lns')
    aug.set('/augeas/load/Php/incl[last() + 1]', CONFIG_FILE)
    aug.load()
    return aug


def get_max_players(aug):
    """Return the maximum players allowed on the server at one time."""
    value = aug.get(AUG_PATH + '/max_users')
    if value:
        return int(value)


def is_creative_mode_enabled(aug):
    """Return whether creative mode is enabled."""
    value = aug.get(AUG_PATH + '/creative_mode')
    return value == 'true'


def is_pvp_enabled(aug):
    """Return whether PVP is enabled."""
    value = aug.get(AUG_PATH + '/enable_pvp')
    return value == 'true'


def is_damage_enabled(aug):
    """Return whether damage is enabled."""
    value = aug.get(AUG_PATH + '/enable_damage')
    return value == 'true'


def get_configuration():
    """Return the current configuration."""
    aug = load_augeas()
    conf = {
        'max_players': get_max_players(aug),
        'creative_mode': is_creative_mode_enabled(aug),
        'enable_pvp': is_pvp_enabled(aug),
        'enable_damage': is_damage_enabled(aug),
    }
    return conf
