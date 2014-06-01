import cherrypy
from modules.auth import require
from plugin_mount import PagePlugin
import cfg
import util


class Services(PagePlugin):
    order = 9 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services")
        self.menu = cfg.main_menu.add_item("Services", "icon-list", "/services", 90)

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect(cfg.server_dir + '/services/xmpp')
