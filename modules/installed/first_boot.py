from urlparse import urlparse
import os, cherrypy, re
from gettext import gettext as _
from plugin_mount import PagePlugin, PluginMount, FormPlugin
from modules.auth import require
from forms import Form
import util as u
from withsqlite.withsqlite import sqlite_db
import cfg
import config

class FirstBoot(PagePlugin):
    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)
        self.register_page("firstboot") # this is the url this page will hang off of (/firstboot)

    @cherrypy.expose
    def index(self, *args, **kwargs):
        return self.state0(*args, **kwargs)

    ## TODO: flesh out these tests values
    def valid_box_key_p(self, key):
        return True
    def generate_box_key(self):
        return "fake key"

    @cherrypy.expose
    def state0(self, message="", hostname="", box_key="", submitted=False):
        """
        In this state, we do time config over HTTP, name the box and
        server key selection.

        All the parameters are form inputs.  They get passed in when
        the form is submitted.  This method checks the inputs and if
        they validate, uses them to take action.  If they do not
        validate, it displays the form to give the user a chance to
        input correct values.  It might display an error message (in
        the message parameter).

        message is an optional string that we can display to the
        user. It's a good place to put error messages.
        """

        ## Until LDAP is in place, we'll put the box name and key in the cfg.store_file
        ## Must resist the sick temptation to write an LDAP interface to the sqlite file
        with sqlite_db(cfg.store_file, table="thisbox", autocommit=True) as db:
            db['about'] = "This table is for information about this FreedomBox"
            if hostname:
                if '' == config.valid_hostname(hostname):
                    config.set_hostname(hostname)
                else:
                    message += _("Invalid box name: %s") % config.valid_hostname(hostname)
            else:
                hostname = config.get_hostname()
            if box_key: 
                if self.valid_box_key_p(box_key):
                    db['box_key'] = box_key
                else:
                    message += _("Invalid key!")
            elif 'box_key' in db and db['box_key']:
                box_key = _("We already have a key for this box on file.") #TODO: Think this through and handle more gracefully
            elif submitted and not box_key:
                box_key = self.generate_box_key()
                db['box_key'] = box_key


        if hostname and box_key and '' == config.valid_hostname(hostname) and self.valid_box_key_p(box_key):
            ## Update state to 1 and head there
            with sqlite_db(cfg.store_file, table="firstboot", autocommit=True) as db:
                db['state']=1
            raise cherrypy.InternalRedirect('/firstboot/state1')

        main = "<p>Welcome.  It looks like this FreedomBox isn't set up yet.  We'll need to ask you a just few questions to get started.</p>"
        form = Form(title="Welcome to Your FreedomBox!", 
                        action="/firstboot", 
                        name="whats_my_name",
                        message=message)
        form.html("<p>For convenience, your FreedomBox needs a name.  It should be something short that doesn't contain spaces or punctuation.  'Willard' would be a good name.  'Freestyle McFreedomBox!!!' would not.</p>")
        form.text_input('Name your FreedomBox', id="hostname", value=hostname)
        form.html("<p>%(hostname)s uses cryptographic keys so it can prove its identity when talking to you.  %(hostname)s can make a key for itself, but if one already exists (from a prior FreedomBox, for example), you can paste it below.  This key should not be the same as your key because you are not your FreedomBox!</p>" % {'hostname':cfg.box_name})
        form.text_box("If you want, paste your box's key here.", id="box_key", value=box_key)
        form.hidden(name="submitted", value="True")
        form.submit("Box it up!")

        main += form.render()
        return self.fill_template(template="base", title=_("First Boot!"), main=main,
        sidebar_right=_("""<strong>Getting Help</strong><p>We've done our best to make your FreedomBox easy to use.  If you have questions during setup, there are a few places to turn for help. TODO: add links to such help.</p>"""))

    @cherrypy.expose
    def state1(self, message=None):
        """
        State 1 is when we have a box name and key.  In this state,
        our task is to provide a certificate and maybe to guide the
        user through installing it.  We automatically move to State 2,
        which is an HTTPS connection.

        TODO: HTTPS failure in State 2 should returns to state 1.
        """
        main = """<p>Here's a certificate.
TODO: explain all this cert stuff to the user.</p>
<p>TODO: add instrux for installing certificate.</p>
<p>After you have installed
"""
        # TODO complete first_boot handling
        # Make sure the user  is not stuck on a dead end for now.
        with sqlite_db(cfg.store_file, table="firstboot", autocommit=True) as db:
            db['state']=5
            main = main + """
<p>Welcome screen not completely implemented yet.  Press <a href="/router">continue</a> to
see the rest of the web interface.</p>"
"""
        
        if False:
            ## Update state to 2 and head there
            with sqlite_db(cfg.store_file, table="firstboot", autocommit=True) as db:
                db['state']=1
                            #TODO: switch to HTTPS
            raise cherrypy.InternalRedirect('/firstboot/state1')

        return self.fill_template(template="base", title=_("Installing the Certificate"), main=main,
        sidebar_right=_("""<strong>Getting Help</strong><p>We've done our best to make your FreedomBox easy to use.  If you have questions during setup, there are a few places to turn for help. TODO: add links to such help.</p>"""))
