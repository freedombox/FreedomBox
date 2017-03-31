#
# This file is part of Plinth.
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

shortcuts = {}


def get_shortcuts():
    """Return menu items in sorted order according to current locale."""
    return sorted(shortcuts.values(), key=lambda item: item['label'])


def add_shortcut(shortcut_id, label, login_required=False,
                 icon=None, url=None,
                 details=None, configure_url=None):
    """Add shortcut to front page."""

    if not url:
        url = '?selected={id}'.format(id=shortcut_id)

    if not icon:
        icon = shortcut_id

    shortcuts[shortcut_id] = {
        'id': shortcut_id,
        'label': label,
        'url': url,
        'icon': icon,
        'login_required': login_required,
        'details': details,
        'configure_url': configure_url,
        'hidden': False
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
    shortcuts = {shortcut_id: shortcut
                 for shortcut_id, shortcut in shortcuts.items()
                 if not match(shortcut)}


def hide_shortcut(shortcut_id, hide=True):
    """Mark a shortcut as hidden or not hidden."""
    global shortcuts
    shortcuts[shortcut_id]['hidden'] = hide
