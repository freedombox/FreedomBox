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
        self.register_page("services.xmpp.configure")
        self.register_page("services.xmpp.register")
        cfg.html_root.services.menu.add_item("XMPP", "icon-comment", "/services/xmpp", 40)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        main = "<p>XMPP Server Accounts and Configuration</p>"
        sidebar_right = '<strong><a href="'+cfg.server_dir+'/services/xmpp/configure">Configure XMPP Server</a></strong><br />'
        sidebar_right = sidebar_right + '<strong><a href="'+cfg.server_dir+'/services/xmpp/register">Register XMPP Account</a></strong>'
        return self.fill_template(title="XMPP Server", main=main, sidebar_right=sidebar_right)

class configure(FormPlugin, PagePlugin):
    url = ["/services/xmpp/configure"]

    sidebar_left = ''
    sidebar_right = _("<strong>Configure XMPP Server</strong>")

    def main(self, inband_enable=False, message=None, *args, **kwargs):
        output, error = privilegedaction_run("xmpp-setup", 'status')
        if error:
            raise Exception("something is wrong: " + error)
        if "inband_enable" in output.split():
            inband_enable = True

        form = Form(title="Configure XMPP Server",
                    action=cfg.server_dir + "/services/xmpp/configure/index",
                    name="configure_xmpp_form",
                    message=message)
        form.checkbox(_("Allow In-Band Registration"), name="inband_enable", 
                        id="inband_enable", checked=inband_enable)
        # hidden field is needed because checkbox doesn't post if not checked
        form.hidden(name="submitted", value="True")
        form.html(_("<p>When enabled, anyone who can reach this server will be allowed to register an account through an XMPP client.</p>"))
        form.submit(_("Update setup"))
        return form.render()

    def process_form(self, inband_enable=None, **kwargs):
        msg = Message()

        if inband_enable == u'on':
            output, error = privilegedaction_run("xmpp-setup", "inband_enable")
            if error:
                raise Exception("something is wrong: " + error)
            msg.add = _("Enabled in-band registration.")
        else:
            output, error = privilegedaction_run("xmpp-setup", "noinband_enable")
            if error:
                raise Exception("something is wrong: " + error)
            msg.add = _("Disabled in-band registration.")

        cfg.log(msg.text)
        main = self.main(inband_enable, msg=msg.text)
        return self.fill_template(title="XMPP Server Configuration", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

class register(FormPlugin, PagePlugin):
    url = ["/services/xmpp/register"]

    sidebar_left = ''
    sidebar_right = _("<strong>Register XMPP Account</strong>")

    def main(self, username='', message=None, *args, **kwargs):
        form = Form(title="Register XMPP Account",
                    action=cfg.server_dir + "/services/xmpp/register/index",
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
            output, error = privilegedaction_run("xmpp-register", [username, password])
            if error:
                raise Exception("something is wrong: " + error)

            if "successfully registered" in output:
                msg.add = _("Registered account for %s." % username)
            else:
                msg.add = _("Failed to register account for %s: %s" % (username, output))

        cfg.log(msg.text)
        main = self.main(username, msg=msg.text)
        return self.fill_template(title="XMPP Server Configuration", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

