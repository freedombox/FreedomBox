import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
import actions
import service
import util


SIDE_MENU = {'title': _('XMPP'),
             'items': [{'url': '/services/xmpp/configure',
                        'text': 'Configure XMPP Server'},
                       {'url': '/services/xmpp/register',
                        'text': 'Register XMPP Account'}]}

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

    @staticmethod
    @cherrypy.expose
    @require()
    def index(**kwargs):
        del kwargs  # Unused
        main = "<p>XMPP Server Accounts and Configuration</p>"

        sidebar_right = util.render_template(template='menu_block',
                                             menu=SIDE_MENU)
        return util.render_template(title="XMPP Server", main=main,
                                    sidebar_right=sidebar_right)

class configure(FormPlugin, PagePlugin):
    url = ["/services/xmpp/configure"]

    @staticmethod
    def sidebar_right(**kwargs):
        """Return rendered string for sidebar on the right"""
        del kwargs  # Unused

        return util.render_template(template='menu_block', menu=SIDE_MENU)

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

        return ''


class register(FormPlugin, PagePlugin):
    url = ["/services/xmpp/register"]

    @staticmethod
    def sidebar_right(**kwargs):
        """Return rendered string for sidebar on the right"""
        del kwargs  # Unused

        return util.render_template(template='menu_block', menu=SIDE_MENU)

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
        msg = util.Message()

        if not username:
            msg.add(_("Must specify a username!"))

        if not password:
            msg.add(_("Must specify a password!"))

        if username and password:
            output, error = actions.superuser_run(
                "xmpp-register", [username, password])
            if error:
                raise Exception("something is wrong: " + error)

            if "successfully registered" in output:
                msg.add(_("Registered account for %s." % username))
            else:
                msg.add(_("Failed to register account for %s: %s" % (username, output)))

        cfg.log(msg.text)

        return msg.text
