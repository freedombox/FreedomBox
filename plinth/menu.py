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

from django.urls import reverse, reverse_lazy


class Menu(object):
    """One menu item."""
    def __init__(self, label="", icon="", url="#", order=50):
        """label is the text that is displayed on the menu.

        icon is the icon to be displayed next to the label.
        Choose from the Glyphicon set:
        http://twitter.github.com/bootstrap/base-css.html#icons

        url is the url location that will be activated when the menu
        item is selected.

        order is the numerical rank of this item within the menu.
        Lower order items appear closest to the top/left of the menu.
        By convention, we use the spectrum between 0 and 100 to rank
        orders, but feel free to disregard that.  If you need more
        granularity, don't bother renumbering things.  Feel free to
        use fractional orders.

        """
        self.label = label
        self.icon = icon
        self.url = url
        self.order = order
        # TODO: With an ordered dictionary for self.items we could access the
        # items by their URL directly instead of searching for them each time,
        # which we do currently with the 'get' method
        self.items = []

    def get(self, urlname, url_args=None, url_kwargs=None):
        """Return a menu item with given URL name."""
        url = reverse(urlname, args=url_args, kwargs=url_kwargs)
        for item in self.items:
            if str(item.url) == url:
                return item

        raise KeyError('Menu item not found')

    def sorted_items(self):
        """Return menu items in sorted order according to current locale."""
        return sorted(self.items, key=lambda x: (x.order, x.label))

    def add_urlname(self, label, icon, urlname, order=50, url_args=None,
                    url_kwargs=None):
        """Add a named URL to the menu (via add_item).

        url_args and url_kwargs will be passed on to Django reverse().

        """
        url = reverse_lazy(urlname, args=url_args, kwargs=url_kwargs)
        return self.add_item(label, icon, url, order)

    def add_item(self, label, icon, url, order=50):
        """Create a new menu item with given parameters, add it to this menu and
        return it.

        """
        item = Menu(label=label, icon=icon, url=url, order=order)
        self.items.append(item)
        return item

    def active_item(self, request):
        """Return the first active item (e.g. submenu) that is found."""
        for item in self.items:
            if request.path.startswith(str(item.url)):
                return item


main_menu = Menu()


def init():
    """Create main menu and other essential menus."""
    main_menu.add_urlname('', 'glyphicon-download-alt', 'apps')
    main_menu.add_urlname('', 'glyphicon-cog', 'system')
