import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
from actions.privilegedactions import privilegedaction_run
from util import Message

class xmpp(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("services.xmpp")
        self.register_page("services.xmpp.register")
        cfg.html_root.services.menu.add_item("XMPP", "icon-comment", "/services/xmpp", 40)

    @cherrypy.expose
    @require()
    def index(self, submitted=False, **kwargs):
        checkedinfo = {
            'inband_enable'    : False,
            }

        if submitted:
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
            privilegedaction_run("xmpp-setup", opts)

        output, error = privilegedaction_run("xmpp-setup", ['status'])
        if error:
            raise Exception("something is wrong: " + error)
        for option in output.split():
            checkedinfo[option] = True

        main = "<p>XMPP Server Configuration</p>"
        form = Form(title="Configuration",
                    action="/services/xmpp",
                    name="configure_xmpp",
                    message='')
        form.checkbox(_("Allow In-Band Registration"), name="xmpp_inband_enable",
                        id="xmpp_inband_enable", checked=checkedinfo['inband_enable'])
        form.hidden(name="submitted", value="True")
        form.html(_("<p>When enabled, anyone who can reach this server will be allowed to register an account through an XMPP client.</p>"))
        form.submit(_("Update setup"))
        main += form.render()

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
            output, error = privilegedaction_run("xmpp-register", [username, password])
            if error:
                raise Exception("something is wrong: " + error)

            if "successfully registered" in output:
                msg.add = _("Registered account for %s." % username)
            else:
                msg.add = _("Failed to register account for %s: %o" % (username, output))

        cfg.log(msg.text)
        main = self.main(username, msg=msg.text)
        return self.fill_template(title="XMPP Server Configuration", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

