import cherrypy
from gettext import gettext as _
from modules.auth import require
from plugin_mount import PagePlugin
from forms import Form
from actions.privilegedactions import privilegedaction_run
import cfg

class Apps(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("apps")
        self.menu = cfg.main_menu.add_item("Apps", "icon-download-alt", "/apps", 80)
        self.menu.add_item("Photo Gallery", "icon-picture", "/apps/photos", 35)
        self.menu.add_item("Owncloud", "icon-picture", "/apps/owncloud", 35)

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
some other website's business model.</p>
""")

    @cherrypy.expose
    @require()
    def owncloud(self, submitted=False, **kwargs):
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
                        action="/apps/owncloud",
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
