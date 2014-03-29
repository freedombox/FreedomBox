import cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin
from modules.auth import require
import cfg

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
        main="""
        <p>Privacy controls are not yet implemented.  This page is a
        placeholder and a promise: privacy is important enough that it
        is a founding consideration, not an afterthought.</p>
        """
        return self.fill_template(title=_("Privacy Control Panel"), main=main,
sidebar_right=_("""<strong>Statement of Principles</strong><p>When we say your
privacy is important, it's not just an empty pleasantry.  We really
mean it.  Your privacy control panel should give you fine-grained
control over exactly who can access your %s and the
information on it.</p>

<p>Your personal information should not leave this box without your
knowledge and direction.  And if companies or government wants this
information, they have to ask <strong>you</strong> for it.  This gives you a
chance to refuse and also tells you who wants your data.</p>
""") % cfg.product_name)
