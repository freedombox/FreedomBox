import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import cfg
import util


class FileExplorer(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sharing.explorer")
        cfg.html_root.sharing.menu.add_item("File Explorer", "icon-folder-open", "/sharing/explorer", 30)

    @cherrypy.expose
    @require()
    def index(self):
        return util.render_template(template='file_explorer',
                                    title=_('File Explorer'))
