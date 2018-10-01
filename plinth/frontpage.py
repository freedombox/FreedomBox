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
Manage application shortcuts on front page.
"""
import json
import os

from plinth import cfg

from . import actions

shortcuts = {}


def get_shortcuts(username=None, web_apps_only=False, sort_by='label'):
    """Return menu items in sorted order according to current locale."""
    shortcuts_to_return = {}
    if username:
        output = actions.superuser_run('users', ['get-user-groups', username])
        user_groups = set(output.strip().split('\n'))

        if 'admin' in user_groups:  # Admin has access to all services
            shortcuts_to_return = shortcuts
        else:
            for shortcut_id, shortcut in shortcuts.items():
                if shortcut['allowed_groups']:
                    if not user_groups.isdisjoint(shortcut['allowed_groups']):
                        shortcuts_to_return[shortcut_id] = shortcut
                else:
                    shortcuts_to_return[shortcut_id] = shortcut
    else:
        shortcuts_to_return = shortcuts

    if web_apps_only:
        shortcuts_to_return = {
            _id: shortcut
            for _id, shortcut in shortcuts_to_return.items()
            if not shortcut['url'].startswith('?selected=')
        }

    return sorted(shortcuts_to_return.values(), key=lambda item: item[sort_by])


def add_custom_shortcuts():
    custom_shortcuts = get_custom_shortcuts()

    if custom_shortcuts:
        for shortcut in custom_shortcuts['shortcuts']:
            web_app_url = _extract_web_app_url(shortcut)
            if web_app_url:
                add_shortcut(None, shortcut['name'],
                             shortcut['short_description'],
                             icon=shortcut['icon_url'], url=web_app_url)


def _extract_web_app_url(custom_shortcut):
    if custom_shortcut.get('clients'):
        for client in custom_shortcut['clients']:
            if client.get('platforms'):
                for platform in client['platforms']:
                    if platform['type'] == 'web':
                        return platform['url']


def get_custom_shortcuts():
    cfg_dir = os.path.dirname(cfg.config_file)
    shortcuts_file = os.path.join(cfg_dir, 'custom-shortcuts.json')
    if os.path.isfile(shortcuts_file) and os.stat(shortcuts_file).st_size:
        with open(shortcuts_file) as shortcuts:
            custom_shortcuts = json.load(shortcuts)
            return custom_shortcuts
    return None


def add_shortcut(shortcut_id, name, short_description="", login_required=False,
                 icon=None, url=None, details=None, configure_url=None,
                 allowed_groups=None):
    """Add shortcut to front page."""

    if not url:
        url = '?selected={id}'.format(id=shortcut_id)

    if not icon:
        icon = shortcut_id

    label = '{0}\n({1})'.format(short_description, name) if short_description \
        else name

    shortcuts[shortcut_id] = {
        'id': shortcut_id,
        'name': name,
        'short_description': short_description,
        'label': label,
        'url': url,
        'icon': icon,
        'login_required': login_required,
        'details': details,
        'configure_url': configure_url,
        'hidden': False,
        'allowed_groups': allowed_groups
    }


def remove_shortcut(shortcut_id):
    """
    Remove shortcut from front page.

    If shortcut_id ends with *, remove all shortcuts with that prefix.
    """

    def match(item):
        if shortcut_id[-1] == '*':
            return item['id'].startswith(shortcut_id[:-1])

        return item['id'] == shortcut_id

    global shortcuts
    shortcuts = {
        shortcut_id: shortcut
        for shortcut_id, shortcut in shortcuts.items() if not match(shortcut)
    }


def hide_shortcut(shortcut_id, hide=True):
    """Mark a shortcut as hidden or not hidden."""
    global shortcuts
    shortcuts[shortcut_id]['hidden'] = hide
