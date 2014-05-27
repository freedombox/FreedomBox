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
        self.menu.add_item("Open ID", "icon-user", "/services/openid", 35)

    @cherrypy.expose
    def index(self):
        return self.openid()

    @cherrypy.expose
    @require()
    def openid(self):
        return util.render_template(template='openid', title="Open ID")
