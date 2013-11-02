import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
import cfg

class Sharing(PagePlugin):
    order = 9 # order of running init in PagePlugins

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sharing")
        self.menu = cfg.main_menu.add_item("Sharing", "icon-share-alt", "/sharing", 35)
        self.menu.add_item("File Server", "icon-inbox", "/sharing/files", 10)

    @cherrypy.expose
    def index(self):
        """This isn't an internal redirect, because we need the url to
        reflect that we've moved down into the submenu hierarchy.
        Otherwise, it's hard to know which menu portion to make active
        or expand or contract."""
        raise cherrypy.HTTPRedirect(cfg.server_dir + '/sharing/files')

    @cherrypy.expose
    @require()
    def files(self):
        return self.fill_template(title="File Server", main='', sidebar_right=_("""
<strong>Freedom NAS</strong><p> The %s can make your spare hard drives accessible to your
local network, thus acting as a NAS server.  We currently support
sharing files via NFS and SMB. 

TODO: this is not true.  We currently support no sharing.</p>
""" % cfg.box_name))

#TODO: move PrinterSharing to another file, as it should be an optional module (most people don't care about printer sharing)
class PrinterSharing(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("sharing.printer")
        cfg.html_root.sharing.menu.add_item("Printer Sharing", "icon-print", "/sharing/printer", 35)

    @cherrypy.expose
    @require()
    def index(self):
        main = """
<p>TODO: Setup and install SAMBA</p>
<p>TODO: Setup and install CUPS</p>
"""
        return self.fill_template(title="Printer Sharing", main=main, sidebar_right="""
<strong>Share Your Printer</strong><p> The %s can share your printer via Samba and CUPS.</p>
""" % cfg.box_name)

 
