import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
from forms import Form
import cfg

class Apps(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps")
        self.menu = cfg.main_menu.add_item("Apps", "icon-download-alt", "/apps", 80)
        self.menu.add_item("Photo Gallery", "icon-picture", "/apps/photos", 35)

    @cherrypy.expose
    def index(self):
        main = """
        <p>User Applications are web apps hosted on your %s.</p>
        
        <p>Eventually this box could be your photo sharing site, your
        instant messaging site, your social networking site, your news
        site.  Remember web portals?  We can be one of those too.
        Many of the services you use on the web could soon be on site
        and under your control!</p>
        """ % (cfg.product_name)
        return self.fill_template(title="User Applications", main=main, sidebar_right='')

    @cherrypy.expose
    @require()
    def photos(self):
        return self.fill_template(title="Photo Gallery", main='', sidebar_right="""
<strong>Photo Gallery</strong><p>Your photos might well be the most valuable
digital property you have, so why trust it to companies that have no
investment in the sentimental value of your family snaps?  Keep those
photos local, backed up, easily accessed and free from the whims of
some other websites business model.</p>
""")

