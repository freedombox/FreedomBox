import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
from forms import Form
import actions
import cfg
import service
from util import Message

class Owncloud(PagePlugin, FormPlugin):
    order = 90

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps.owncloud")
        cfg.html_root.apps.menu.add_item("Owncloud", "icon-picture", "/apps/owncloud", 35)

        self.service = service.Service('owncloud', _('ownCloud'),
                                       ['http', 'https'], is_external=True,
                                       enabled=self.is_enabled)

    def is_enabled(self):
        """Return whether ownCloud is enabled"""
        output, error = actions.run('owncloud-setup', 'status')
        if error:
            raise Exception('Error getting ownCloud status: %s' % error)

        return 'enable' in output.split()

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        owncloud_enable = self.is_enabled()

        if 'submitted' in kwargs:
            owncloud_enable = self.process_form(kwargs)
        
        main = self.form(owncloud_enable)
        sidebar_right="""
<strong>ownCloud</strong></br>
<p>ownCloud gives you universal access to your files through a web interface or WebDAV. It also provides a platform to easily view & sync your contacts, calendars and bookmarks across all your devices and enables basic editing right on the web. Installation has minimal server requirements, doesn't need special permissions and is quick. ownCloud is extendable via a simple but powerful API for applications and plugins.
</p>
"""
        return self.fill_template(title="Owncloud", main=main, sidebar_right=sidebar_right)

    def form(self, owncloud_enable, message=None):
        form = Form(title="Configuration",
                        action=cfg.server_dir + "/apps/owncloud/index",
                        name="configure_owncloud",
                        message=message)
        form.checkbox(_("Enable Owncloud"), name="owncloud_enable", id="owncloud_enable", checked=owncloud_enable)
        # hidden field is needed because checkbox doesn't post if not checked
        form.hidden(name="submitted", value="True")
        form.html(_("""<p>When enabled, the owncloud installation will be available from <a href="/owncloud">owncloud</a> on the web server.   Visit this URL to set up the initial administration account for owncloud.</p>"""))
        form.html(_("""<p><strong>Note: Setting up owncloud for the first time might take 5 minutes or more, depending on download bandwidth from the Debian APT sources.</p>"""))
        form.submit(_("Update setup"))
        return form.render()

    def process_form(self, kwargs):
        checkedinfo = {
            'enable'   : False,
        }

        opts = []
        for k in kwargs.keys():
            if 'on' == kwargs[k]:
                shortk = k.split("owncloud_").pop()
                checkedinfo[shortk] = True

            for key in checkedinfo.keys():
                if checkedinfo[key]:
                    opts.append(key)
                else:
                    opts.append('no'+key)
        actions.superuser_run("owncloud-setup", opts, async=True)

        # Send a signal to other modules that the service is
        # enabled/disabled
        self.service.notify_enabled(self, checkedinfo['enable'])

        return checkedinfo['enable']
