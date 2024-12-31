# SPDX-License-Identifier: AGPL-3.0-or-later

from typing import ClassVar

from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from plinth import app


class Menu(app.FollowerComponent):
    """Component to manage a single menu item."""

    _all_menus: ClassVar[set['Menu']] = set()

    def __init__(self, component_id: str, name: str | None = None,
                 icon: str | None = None, tags: list[str] | None = None,
                 url_name: str | None = None, url_args: list | None = None,
                 url_kwargs: dict | None = None,
                 parent_url_name: str | None = None, order: int = 50,
                 advanced: bool = False):
        """Initialize a new menu item with basic properties.

        name is the label of the menu item.

        icon is the icon to be displayed for the menu item. Icon can be the
        name of a glyphicon from the Fork Awesome font's icon set:
        https://forkawesome.github.io/Fork-Awesome/icons/. In this case, the
        icon name starts with the string 'fa-'. Alternatively, the icon can
        also be a file under the directory plinth/modules/<app>/static/icons/,
        provided without an extension. SVG icons are preferred. Currently, both
        PNG and SVG icons with the same name are used. For example, if the
        value of icon is 'myicon' and app_id in App class is 'myapp', then two
        icons files plinth/modules/myapp/static/icons/myicon.svg and
        plinth/modules/myapp/static/icons/myicon.png are used in the interface.

        tags is a list of tags that describe the app. Tags help users to find
        similar apps or alternatives and discover use cases.

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
        self.icon = icon
        self.tags = tags
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

    @staticmethod
    def get_with_url_name(url_name: str) -> 'Menu':
        """Return a menu item with given URL name.

        Raise LookupError of the request item is not found.
        """
        for item in Menu._all_menus:
            if item.url_name == url_name:
                return item

        raise LookupError


main_menu = None


def init():
    """Create main menu and other essential menus."""
    global main_menu
    main_menu = Menu('menu-index', name=_('Home'), url_name='index')
    Menu('menu-apps', name=_('Apps'), icon='fa-download', url_name='apps',
         parent_url_name='index')
    Menu('menu-system', name=_('System'), icon='fa-cog', url_name='system',
         parent_url_name='index')

    Menu('menu-system-visibility', name=_('Visibility'), icon='fa-cog',
         url_name='system:visibility', parent_url_name='system', order=10)
    Menu('menu-system-data', name=_('Data'), icon='fa-cog',
         url_name='system:data', parent_url_name='system', order=20)
    Menu('menu-system-system', name=_('System'), icon='fa-cog',
         url_name='system:system', parent_url_name='system', order=30)
    Menu('menu-system-security', name=_('Security'), icon='fa-cog',
         url_name='system:security', parent_url_name='system', order=40)
    Menu('menu-system-administration', name=_('Administration'), icon='fa-cog',
         url_name='system:administration', parent_url_name='system', order=50)
