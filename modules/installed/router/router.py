import cherrypy
from django import forms
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
import cfg
import util


class Router(PagePlugin):
    """Router page"""
    order = 9  # order of running init in PagePlugins

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, args, kwargs)

        self.register_page('router')

        self.menu = cfg.main_menu.add_item('Router', 'icon-retweet', '/router',
                                           10)

    @staticmethod
    @cherrypy.expose
    def index():
        """This isn't an internal redirect, because we need the url to
        reflect that we've moved down into the submenu hierarchy.
        Otherwise, it's hard to know which menu portion to make active
        or expand or contract."""
        raise cherrypy.HTTPRedirect(cfg.server_dir + '/router/pagekite')
