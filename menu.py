from urlparse import urlparse
import cherrypy
import cfg


class Menu():
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
        self.items = []

    def sort_items(self):
        """Sort the items in self.items by order."""
        self.items = sorted(self.items, key=lambda x: x.order, reverse=False)

    def add_item(self, label, icon, url, order=50, basehref=True):
        """This method creates a menu item with the parameters, adds
        that menu item to this menu, and returns the item.

        If BASEHREF is true and url start with a slash, prepend the
        cfg.server_dir to it"""

        if basehref and url.startswith("/"):
            url = cfg.server_dir + url

        item = Menu(label=label, icon=icon, url=url, order=order)
        self.items.append(item)
        self.sort_items()
        return item

    def active_p(self):
        """Returns True if this menu item is active, otherwise False.

        We can tell if a menu is active if the menu item points
        anywhere above url we are visiting in the url tree."""
        return urlparse(cherrypy.url()).path.startswith(self.url)

    def active_item(self):
        """Return item list (e.g. submenu) of active menu item."""
        path = urlparse(cherrypy.url()).path
        for item in self.items:
            if path.startswith(item.url):
                return item
