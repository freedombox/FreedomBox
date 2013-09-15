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

class experts(FormPlugin, PagePlugin):
    url = ["/sys/config"]
    order = 10

    def help(self, *args, **kwargs):
        side = _(#"""<strong>Expert Mode</strong>
        """ 
        <p>The %(box)s can be administered in two modes, 'basic'
        and 'expert'.  Basic mode hides a lot of features and
        configuration options that most users will never need to think
        about.  Expert mode allows you to get into the details.</p>

        <p>Most users can operate the %(box)s by configuring the
        limited number of options visible in Basic mode.  For the sake
        of simplicity and ease of use, we hid most of %(product)s's
        less frequently used options.  But if you want more
        sophisticated features, you can enable Expert mode, and
        %(product)s will present more advanced menu options.</p>

        <p>You should be aware that it might be possible to render
        your %(box)s inaccessible via Expert mode options.</p>
        """ % {'box':cfg.box_name, 'product':cfg.product_name})

        return side

    def main(self, expert=None, message='', **kwargs):
        """Note that kwargs contains '':"submit" if this is coming
        from a submitted form.  If kwargs is empty, it's a fresh form
        with no user input, which means it should just reflect the
        state of the stored data."""
        if not kwargs and expert == None:
            expert = cfg.users.expert()
            cfg.log("Expert mode is %s" % expert)
        form = Form(title=_("Expert Mode"), 
                        action="/sys/config/experts", 
                        name="expert_mode_form",
                        message=message )
        form.html(self.help())
        form.checkbox(_("Expert Mode"), name="expert", checked=expert)
        form.submit(_("Submit"))
        return form.render()

    def process_form(self, expert='', *args, **kwargs):
        user = cfg.users.get()

        message = 'settings unchanged'

        if expert:
            if not 'expert' in user['groups']:
                user['groups'].append('expert')
                message = "enabled"
        else:
            if 'expert' in user['groups']:
                user['groups'].remove('expert')
                message = "disabled"

        cfg.users.set(user)
        return "Expert mode %s." % message
