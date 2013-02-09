from urlparse import urlparse
import os, cherrypy
from gettext import gettext as _
from plugin_mount import PagePlugin, PluginMount, FormPlugin
from modules.auth import require
from forms import Form
import util as u
from vendor.withsqlite.withsqlite import sqlite_db
import cfg

class FirstBoot(PagePlugin):
    order = 0 # order of running init in PagePlugins
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("firstboot") # this is the url this page will hang off of (/firstboot)
        #self.menu = cfg.main_menu.add_item("First Boot", "icon-eye-open", "/privacy", 12)
        #self.menu.add_item("General Config", "icon-asterisk", "/privacy/config", 10)
        #self.menu.add_item("Ad Blocking", "icon-ban-circle", "/privacy/adblock", 20)
        #self.menu.add_item("TOR", "icon-eye-close", "/privacy/TOR", 30)
        #self.menu.add_item("HTTPS Everywhere", "icon-lock", "/privacy/https_everywhere", 30)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        return self.state0(*args, **kwargs)

    @cherrypy.expose
    @require()
    def state0(self, message=None, box_name=None, box_key=""):
        """
        All the parameters are form inputs.  They get passed in when
        the form is submitted.  This method checks the inputs and if
        they validate, uses them to take action.  If they do not
        validate, it displays the form to give the user a chance to
        input correct values.  It might display an error message (in
        the message parameter).

        message is an optional string that we can display to the
        user. It's a good place to put error messages.
        """

        

        form = Form(title="Welcome to Your FreedomBox!", 
                        action="/firstboot", 
                        name="whats_my_name",
                        message=message)
        if not box_name:
            box_name = cfg.box_name
        form.html("<p>For convenience, your FreedomBox needs a name.  It should be something short that doesn't contain spaces or punctuation.  'Willard' would be a good name.  'Freestyle McFreedomBox!!!' would not.</p>")
        form.text_input('Name your FreedomBox', id="box_name", value=box_name)
        form.html("<p>%(box_name)s uses cryptographic keys so it can prove its identity when talking to you.  %(box_name)s can make a key for you, but if you already have one (from a prior FreedomBox, maybe), you can paste it below.  This key should not be the same as your key because you are not your FreedomBox!</p>" % {'box_name':cfg.box_name})
        form.text_box("If you want, paste your box's key here.", id="box_key", value=box_key)
        form.submit("Box it up!")

        main=form.render()
        return main
        return self.fill_template(title=_("Privacy Control Panel"), main=main,
sidebar_right=_("""<strong>Statement of Principles</strong><p>When we say your
privacy is important, it's not just an empty pleasantry.  We really
mean it.  Your privacy control panel should give you fine-grained
control over exactly who can access your %s and the
information on it.</p>

<p>Your personal information should not leave this box without your
knowledge and direction.  And if companies or government wants this
information, they have to ask <strong>you</strong> for it.  This gives you a
change to refuse and also tells you who wants your data.</p>
""") % cfg.product_name)
