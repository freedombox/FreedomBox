import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import cfg
import util


class Apps(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps")
        self.menu = cfg.main_menu.add_item("Apps", "icon-download-alt", "/apps", 80)
        self.menu.add_item("Chat", "icon-comment", "/../jwchat", 30)
        self.menu.add_item("Photo Gallery", "icon-picture", "/apps/photos", 35)

    @cherrypy.expose
    def index(self):
        return util.render_template(template='apps',
                                    title=_('User Applications'))

    @cherrypy.expose
    @require()
    def photos(self):
        return util.render_template(template='photos',
                                    title=_('Photo Gallery'))
