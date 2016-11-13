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


def add_shortcut(id, label, url, icon, login_required, details=None):
    """Add shortcut to front page."""
    apps_login_required = {'deluge', 'openvpn', 'quassel', 'radicale', 'repro',
                           'roundcube', 'shaarli', 'transmission', 'ttrss',
                           'xmpp', 'privoxy'}

    if not url:
        url = '?selected={id}'.format(id=id)
    if id in apps_login_required:
        login_required = True
    else:
        login_required = False

    shortcuts[id] = {
        'id': id,
        'label': label,
        'url': url,
        'icon': icon,
        'details': details,
        'login_required': login_required,
    }


def remove_shortcut(id):
    """
    Remove shortcut from front page.

    If id ends with *, remove all shortcuts with that prefix.
    """
    def match(item):
        if id[-1] == '*':
            return item['id'].startswith(id[:-1])

        return item['id'] == id

    global shortcuts
    shortcuts = {id: shortcut
                 for id, shortcut in shortcuts.items()
                 if not match(shortcut)}
