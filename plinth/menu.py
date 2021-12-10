# SPDX-License-Identifier: AGPL-3.0-or-later

from django.urls import reverse_lazy

from plinth import app


class Menu(app.FollowerComponent):
    """Component to manage a single menu item."""

    _all_menus = set()

    def __init__(self, component_id, name=None, short_description=None,
                 icon=None, url_name=None, url_args=None, url_kwargs=None,
                 parent_url_name=None, order=50, advanced=False):
        """Initialize a new menu item with basic properties.

        name is the label of the menu item.

        short_description is an optional description shown on the menu item.

        icon is the icon to be displayed for the menu item. Icon can be the
        name of a glyphicon from the Fork Awesome font's icon set:
        https://forkawesome.github.io/Fork-Awesome/icons/. In this case, the
        icon name starts with the string 'fa-'. Alternatively, the icon can
        also be a file under the directory static/theme/icons/, provided
        without an extension. SVG icons are preferred. Currently, both PNG and
        SVG icons with the same name are used. For example, if the value of
        icon is 'myapp', then two icons files static/theme/icons/myapp.svg and
        static/theme/icons/myapp.png are used in the interface.

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

        self.url_name = url_name
        self.url_args = url_args
        self.url_kwargs = url_kwargs
        self.parent_url_name = parent_url_name

        # Add self to global list of menu items.
        self._all_menus.add(self)

    @property
    def items(self):
        """Return the list of children for this menu item."""
        return [
            item for item in self._all_menus
            if item.parent_url_name == self.url_name
        ]

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
