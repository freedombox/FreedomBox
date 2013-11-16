import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
from forms import Form
from privilegedactions import privilegedaction_run
import cfg
from util import Message

class Owncloud(PagePlugin):
    order = 90

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps.owncloud")
        self.register_page("apps.owncloud.configure")
        cfg.html_root.apps.menu.add_item("Owncloud", "icon-picture", "/apps/owncloud", 35)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        sidebar_right="""
<strong>Owncloud</strong><p>gives you universal access to your files through a web interface or WebDAV. It also provides a platform to easily view & sync your contacts, calendars and bookmarks across all your devices and enables basic editing right on the web. Installation has minimal server requirements, doesn't need special permissions and is quick. ownCloud is extendable via a simple but powerful API for applications and plugins.
</p>
"""
        sidebar_right = sidebar_right + '<strong><a href="'+cfg.server_dir+'/apps/owncloud/configure">Configure Owncloud</a></strong>'
        return self.fill_template(title="Owncloud", main='', sidebar_right=sidebar_right)

class configure(FormPlugin, PagePlugin):
    url = ["/apps/owncloud/configure"]

    sidebar_left = ''
    sidebar_right = _("<strong>Configure Owncloud</strong>")

    def main(self, owncloud_enable=False, message=None, *args, **kwargs):
        output, error = privilegedaction_run("owncloud-setup", 'status')
        if error:
            raise Exception("something is wrong: " + error)
        if "enable" in output.split():
            owncloud_enable = True

        form = Form(title="Configuration",
                        action=cfg.server_dir + "/apps/owncloud/configure/index",
                        name="configure_owncloud",
                        message=message)
        form.checkbox(_("Enable Owncloud"), name="owncloud_enable", id="owncloud_enable", checked=owncloud_enable)
        # hidden field is needed because checkbox doesn't post if not checked
        form.hidden(name="submitted", value="True")
        form.html(_("<p>When enabled, the owncloud installation will be available from /owncloud/ on the web server.</p>"))
        form.submit(_("Update setup"))
        return form.render()

    def process_form(self, owncloud_enable=None, **kwargs):
        msg = Message()

        if owncloud_enable == u'on':
            output, error = privilegedaction_run("owncloud-setup", "enable")
            if error:
                raise Exception("something is wrong: " + error)
            msg.add = _("Enabled Owncloud.")
        else:
            output, error = privilegedaction_run("owncloud-setup", "noenable")
            if error:
                raise Exception("something is wrong: " + error)
            msg.add = _("Disabled Owncloud.")

        cfg.log(msg.text)
        main = self.main(owncloud_enable, msg=msg.text)
        return self.fill_template(title="Owncloud Configuration", main=main, sidebar_left=self.sidebar_left, sidebar_right=self.sidebar_right)

