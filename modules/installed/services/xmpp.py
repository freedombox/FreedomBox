import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
import actions
import service
from util import Message

class xmpp(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services.xmpp")
        self.register_page("services.xmpp.configure")
        self.register_page("services.xmpp.register")
        cfg.html_root.services.menu.add_item("XMPP", "icon-comment", "/services/xmpp", 40)

        self.client_service = service.Service(
            'xmpp-client', _('Chat Server - client connections'),
            is_external=True, enabled=True)
        self.server_service = service.Service(
            'xmpp-server', _('Chat Server - server connections'),
            is_external=True, enabled=True)
        self.bosh_service = service.Service(
            'xmpp-bosh', _('Chat Server - web interface'), is_external=True,
            enabled=True)

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

    def main(self, xmpp_inband_enable=False, message=None, *args, **kwargs):
        output, error = actions.superuser_run("xmpp-setup", 'status')
        if error:
            raise Exception("something is wrong: " + error)
        if "inband_enable" in output.split():
            xmpp_inband_enable = True

        form = Form(title="Configure XMPP Server",
                    action=cfg.server_dir + "/services/xmpp/configure/index",
                    name="configure_xmpp_form",
                    message=message)
        form.checkbox(_("Allow In-Band Registration"), name="xmpp_inband_enable",
                        id="xmpp_inband_enable", checked=xmpp_inband_enable)
        # hidden field is needed because checkbox doesn't post if not checked
        form.hidden(name="submitted", value="True")
        form.html(_("<p>When enabled, anyone who can reach this server will be allowed to register an account through an XMPP client.</p>"))
        form.submit(_("Update setup"))
        return form.render()

    def process_form(self, **kwargs):
        checkedinfo = {
            'inband_enable' : False,
        }

        opts = []
        for k in kwargs.keys():
            if 'on' == kwargs[k]:
                shortk = k.split("xmpp_").pop()
                checkedinfo[shortk] = True

            for key in checkedinfo.keys():
                if checkedinfo[key]:
                    opts.append(key)
                else:
                    opts.append('no'+key)
        actions.run("xmpp-setup", opts)

        main = self.main(checkedinfo['inband_enable'])
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
            output, error = actions.superuser_run(
                "xmpp-register", [username, password])
            if error:
                raise Exception("something is wrong: " + error)

            if "successfully registered" in output:
                msg.add = _("Registered account for %s." % username)
            else:
                msg.add = _("Failed to register account for %s: %s" % (username, output))

        cfg.log(msg.text)
        main = self.main(username, msg=msg.text)
        return self.fill_template(
            title="XMPP Server Configuration",
            main=main,
            sidebar_left=self.sidebar_left,
            sidebar_right=self.sidebar_right)
