import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
import cfg
import util


class Privacy(PagePlugin):
    order = 20 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("privacy")
        self.menu = cfg.main_menu.add_item("Privacy", "icon-eye-open", "/privacy", 12)
        self.menu.add_item("General Config", "icon-asterisk", "/privacy/config", 10)
        self.menu.add_item("Ad Blocking", "icon-ban-circle", "/privacy/adblock", 20)
        self.menu.add_item("HTTPS Everywhere", "icon-lock", "/privacy/https_everywhere", 30)

    @cherrypy.expose
    def index(self):
        #raise cherrypy.InternalRedirect('/privacy/config')
        return self.config()

    @cherrypy.expose
    @require()
    def config(self):
        return util.render_template(template='privacy_config',
                                    title=_('Privacy Control Panel'))
