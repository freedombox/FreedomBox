import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
import cfg
import util


class Sys(PagePlugin):
    order = 10

    def __init__(self):
        super(Sys, self).__init__()

        self.register_page("sys")
        self.menu = cfg.main_menu.add_item(_("System"), "icon-cog", "/sys", 100)
        self.menu.add_item(_("Users and Groups"), "icon-user", "/sys/users", 15)

    @cherrypy.expose
    def index(self):
        return util.render_template(template='system',
                                    title=_("System Configuration"))
