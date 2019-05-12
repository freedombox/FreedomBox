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

from django.urls import reverse, reverse_lazy

from plinth import app


class Menu(app.FollowerComponent):
    """Component to manage a single menu item."""

    _all_menus = {}

    def __init__(self, component_id, name=None, short_description=None,
                 icon=None, url_name=None, url_args=None, url_kwargs=None,
                 parent_url_name=None, order=50, advanced=False):
        """Initialize a new menu item with basic properties.

        name is the label of the menu item.

        short_description is an optional description shown on the menu item.

        icon is the icon to be displayed for the menu item. Choose from the
        Fork Awesome set: https://forkawesome.github.io/Fork-Awesome/icons/

        url_name is the name of url location that will be activated when the
        menu item is selected. This is not optional. url_args and url_kwargs
        are sent to reverse() when resolving url from url_name.

        parent_url_name optionally specifies the menu item under which this
        menu item should become a child.

        order is the numerical rank of this item within the menu. Lower order
        items appear closest to the top/left of the menu. By convention, we use
        the spectrum between 0 and 100 to rank orders, but feel free to
        disregard that. If you need more granularity, don't bother renumbering
        things. Feel free to use fractional orders.

        advanced decides whether to show the menu item only in advanced mode.

        """
        super().__init__(component_id)
        if not url_name:
            raise ValueError('Valid url_name is expected')

        url = reverse_lazy(url_name, args=url_args, kwargs=url_kwargs)

        self.name = name
        self.short_description = short_description
        self.icon = icon
        self.url = url
        self.order = order
        self.advanced = advanced
        self.items = []

        # Add self to parent menu item
        if parent_url_name:
            parent_menu = self.get(parent_url_name)
            parent_menu.items.append(self)

        # Add self to global list of menu items
        self._all_menus[url] = self

    @classmethod
    def get(cls, urlname, url_args=None, url_kwargs=None):
        """Return a menu item with given URL name."""
        url = reverse(urlname, args=url_args, kwargs=url_kwargs)
        return cls._all_menus[url]

    def sorted_items(self):
        """Return menu items in sorted order according to current locale."""
        return sorted(self.items, key=lambda x: (x.order, x.name.lower()))

    def active_item(self, request):
        """Return the first active item (e.g. submenu) that is found."""
        for item in self.items:
            if request.path.startswith(str(item.url)):
                return item

        return None


main_menu = None


def init():
    """Create main menu and other essential menus."""
    global main_menu
    main_menu = Menu('menu-index', url_name='index')
    Menu('menu-apps', icon='fa-download', url_name='apps',
         parent_url_name='index')
    Menu('menu-system', icon='fa-cog', url_name='system',
         parent_url_name='index')
