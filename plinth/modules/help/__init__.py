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
FreedomBox app for help pages.
"""

from django.utils.translation import ugettext_lazy as _

from plinth import menu
from plinth.app import App

version = 1

is_essential = True
app = None


class HelpApp(App):
    """FreedomBox app for showing help."""

    app_id = 'help'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        menu_item = menu.Menu('menu-help', _('Documentation'), None, 'fa-book',
                              'help:index', parent_url_name='index')
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-manual', _('Manual'), None,
                              'fa-info-circle', 'help:manual',
                              parent_url_name='help:index', order=10)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-support', _('Get Support'), None,
                              'fa-life-ring', 'help:support',
                              parent_url_name='help:index', order=20)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-feedback', _('Submit Feedback'), None,
                              'fa-comments', 'help:feedback',
                              parent_url_name='help:index', order=25)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-contribute', _('Contribute'), None,
                              'fa-wrench', 'help:contribute',
                              parent_url_name='help:index', order=30)
        self.add(menu_item)
        menu_item = menu.Menu('menu-help-about', _('About'), None, 'fa-star',
                              'help:about', parent_url_name='help:index',
                              order=100)
        self.add(menu_item)


def init():
    """Initialize the Help module"""
    global app
    app = HelpApp()
    app.set_enabled(True)
