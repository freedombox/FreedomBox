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

    @cherrypy.expose
    def index(self):
        return util.render_template(template='privacy_config',
                                    title=_('Privacy Control Panel'))
