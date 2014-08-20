from django.core.urlresolvers import reverse


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
            if item.url == url:
                return item

        raise KeyError('Menu item not found')

    def sort_items(self):
        """Sort the items in self.items by order."""
        self.items = sorted(self.items, key=lambda x: x.order, reverse=False)

    def add_urlname(self, label, icon, urlname, order=50, url_args=None,
                    url_kwargs=None):
        """Add a named URL to the menu (via add_item).

        url_args and url_kwargs will be passed on to Django reverse().

        """
        url = reverse(urlname, args=url_args, kwargs=url_kwargs)
        return self.add_item(label, icon, url, order)

    def add_item(self, label, icon, url, order=50):
        """Create a new menu item with given parameters, add it to this menu and
        return it.

        """
        item = Menu(label=label, icon=icon, url=url, order=order)
        self.items.append(item)
        self.sort_items()
        return item

    def active_item(self, request):
        """Return the first active item (e.g. submenu) that is found."""
        for item in self.items:
            if request.path.startswith(item.url):
                return item
