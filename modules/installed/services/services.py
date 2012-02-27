import cherrypy
from modules.auth import require
from plugin_mount import PagePlugin
import cfg

class Services(PagePlugin):
    order = 9 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services")
        self.menu = cfg.main_menu.add_item("Services", "/services", 90)
        self.menu.add_item("Open ID", "/services/openid", 35)

    @cherrypy.expose
    def index(self):
        return self.openid()

    @cherrypy.expose
    @require()
    def openid(self):
        return self.fill_template(title="Open ID", main='', sidebar_right="""
<strong>One Login for Every Site</strong><p>Your %s is also an OpenID
machine.  It can generate credentials that allow you to log in to many
websites without the need to remember or enter a separate username and
password at each one.</p>
""" % cfg.box_name)
