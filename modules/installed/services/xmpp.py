import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
from privilegedactions import privilegedaction_run
from util import Message

class xmpp(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services.xmpp")
        self.register_page("services.xmpp.register")
        cfg.html_root.services.menu.add_item("XMPP", "icon-comment", "/services/xmpp", 40)

    @cherrypy.expose
    @require()
    def index(self):
        main = "<p>XMPP Server Configuration</p>"
        sidebar_right = """
<strong><a href="/services/xmpp/register">Register XMPP Account</a></strong>
"""
        return self.fill_template(title="XMPP Server Configuration", main=main, sidebar_right=sidebar_right)

class register(FormPlugin, PagePlugin):
    url = ["/services/xmpp/register"]

    sidebar_left = ''
    sidebar_right = _("<strong>Register XMPP Account</strong>")

    def main(self, username='', message=None, *args, **kwargs):
        form = Form(title="Register XMPP Account",
                    action="/services/xmpp/register/index",
                    name="register_xmpp_form",
                    message=message)
        form.text_input(_("Username"), name="username", value=username)
        form.text_input(_("Password"), name="password", type="password")
        form.submit(label=_("Register XMPP Account"), name="register")
        return form.render()

    def process_form(self, username=None, password=None, **kwargs):
        msg = Message()

        if not username: msg.add = _("Must specify a username!")
        if not password: msg.add = _("Must specify a password!")

        if username and password:
            privilegedaction_run("xmpp-register", [username, password])
            msg.add = _("Registered account for %s." % username)

        cfg.log(msg.text)
        main = self.main(username, msg=msg.text)
        return self.fill_template(title="XMPP Server Configuration", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

