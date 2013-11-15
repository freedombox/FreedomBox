import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
from forms import Form
from privilegedactions import privilegedaction_run
import cfg

class Owncloud(PagePlugin):
    order = 90

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps.owncloud")
        cfg.html_root.apps.menu.add_item("Owncloud", "icon-picture", "/apps/owncloud", 35)

    @cherrypy.expose
    @require()
    def index(self, submitted=False, **kwargs):
        checkedinfo = {
            'enable'   : False,
            }

        if submitted:
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
            privilegedaction_run("owncloud-setup", opts)

        output, error = privilegedaction_run("owncloud-setup", ['status'])
        if error:
            raise Exception("something is wrong: " + error)
        for option in output.split():
            checkedinfo[option] = True

        main="""
"""
        form = Form(title="Configuration", 
                        action=cfg.server_dir + "/apps/owncloud", 
                        name="configure_owncloud",
                        message='')
        form.checkbox(_("Enable Owncloud"), name="owncloud_enable", id="owncloud_enable", checked=checkedinfo['enable'])
        form.hidden(name="submitted", value="True")
        form.html(_("<p>When enabled, the owncloud installation will be available from /owncloud/ on the web server.</p>"))
        form.submit(_("Update setup"))
        main += form.render()
        sidebar_right="""
<strong>Owncloud</strong><p>gives you universal access to your files through a web interface or WebDAV. It also provides a platform to easily view & sync your contacts, calendars and bookmarks across all your devices and enables basic editing right on the web. Installation has minimal server requirements, doesn't need special permissions and is quick. ownCloud is extendable via a simple but powerful API for applications and plugins.
</p>
"""
        return self.fill_template(title="Owncloud", main=main, sidebar_right=sidebar_right)
        
