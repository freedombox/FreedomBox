import os
import cherrypy
try:
    import simplejson as json
except ImportError:
    import json
from gettext import gettext as _
from filedict import FileDict
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import cfg
from forms import Form
from model import User
from util import *

class wan(FormPlugin, PagePlugin):
    url = ["/sys/config"]
    order = 20

    def help(self, *args, **kwargs):
        if not cfg.users.expert():
            return ''
        return _(#"""<h4>Admin from WAN</h4>
        """<p>If you check this box, this front
        end will be reachable from the WAN.  If your %(box)s
        connects you to the internet, that means you'll be able to log
        in to the front end from the internet.  This might be
        convenient, but it is also <strong>dangerous</strong>, since it can
        enable attackers to gain access to your %(box)s from the
        outside world.  All they'll need is your username and
        passphrase, which they might guess or they might simply try
        every posible combination of letters and numbers until they
        get in.  If you enable the WAN administration option, you
        <strong>must</strong> use long and complex passphrases.</p>

        <p>For security reasons, neither WAN Administration nor WAN
        SSH is available to the `admin` user account.</p>

        <p>TODO: in expert mode, tell user they can ssh in to enable
        admin from WAN, do their business, then disable it.  It would
        be good to enable the option and autodisable it when the ssh
        connection dies.</p>
        """ % {'product':cfg.product_name, 'box':cfg.box_name})

    def main(self, message='', **kwargs):
        store = filedict_con(cfg.store_file, 'sys')

        defaults = {'wan_admin': "''",
                    'wan_ssh': "''",
                    'lan_ssh': "''",
                    }
        for k,c in defaults.items():
            if not k in kwargs:
                try:
                    kwargs[k] = store[k]
                except KeyError:
                    exec("if not '%(k)s' in kwargs: store['%(k)s'] = kwargs['%(k)s'] = %(c)s" % {'k':k, 'c':c})

        form = Form(title=_("Accessing the %s" % cfg.box_name), 
                        action="/sys/config/wan", 
                        name="admin_wan_form",
                        message=message )
        form.html(self.help())
        if cfg.users.expert():
            form.checkbox(_("Allow access to Plinth from WAN"), name="wan_admin", checked=kwargs['wan_admin'])
            form.checkbox(_("Allow SSH access from LAN"), name="lan_ssh", checked=kwargs['lan_ssh'])
            form.checkbox(_("Allow SSH access from WAN"), name="wan_ssh", checked=kwargs['wan_ssh'])
        form.submit(_("Submit"))
        return form.render()

    def process_form(self, wan_admin='', wan_ssh='', lan_ssh='', *args, **kwargs):
        store = filedict_con(cfg.store_file, 'sys')
        for field in ['wan_admin', 'wan_ssh', 'lan_ssh']:
            exec("store['%s'] = %s" % (field, field))
        return "Settings updated."

