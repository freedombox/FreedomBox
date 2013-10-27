import os, subprocess
from socket import gethostname
import cherrypy
try:
    import simplejson as json
except ImportError:
    import json
from gettext import gettext as _
from filedict import FileDict
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
from actions.privilegedactions import privilegedaction_run
import cfg
import re
from forms import Form
from model import User
from util import *
import platform

class Config(PagePlugin):
    def __init__(self, *args, **kwargs):
        self.register_page("sys.config")

    @cherrypy.expose
    @require()
    def index(self):
        parts = self.forms('/sys/config')
        parts['title']=_("Configure this %s" % cfg.box_name)
        return self.fill_template(**parts)

def valid_hostname(name):
    """Return '' if name is a valid hostname by our standards (not
    just by RFC 952 and RFC 1123.  We're more conservative than the
    standard.  If hostname isn't valid, return message explaining why."""

    message = ''
    if len(name) > 63:
        message += "<br />Hostname too long (max is 63 characters)"

    if not is_alphanumeric(name):
        message += "<br />Hostname must be alphanumeric"

    if not bool(re.match("A-z", name[0])):
        message += "<br />Hostname must start with a letter"

    return message

def get_hostname():
    return gethostname()

def set_hostname(hostname):
    "Sets machine hostname to hostname"
    cfg.log.info("Changing hostname to '%s'" % hostname)
    try:
        privilegedaction_run("hostname-change", [hostname])
    except OSError, e:
        raise cherrypy.HTTPError(500, "Updating hostname failed: %s" % e)
    else:
        # don't persist/cache change unless it was saved successfuly
        sys_store = filedict_con(cfg.store_file, 'sys')
        sys_store['hostname'] = hostname

class general(FormPlugin, PagePlugin):
    url = ["/sys/config"]
    order = 30

    def help(self, *args, **kwargs):
        return _(#"""<strong>Time Zone</strong>
        """<p>Set your timezone to get accurate
        timestamps.  %(product)s will use this information to set your
        %(box)s's systemwide timezone.</p>
        """ % {'product':cfg.product_name, 'box':cfg.box_name})

    def main(self, message='', **kwargs):
        if not cfg.users.expert():
            return '<p>' + _('Only members of the expert group are allowed to see and modify the system setup.') + '</p>'

        sys_store = filedict_con(cfg.store_file, 'sys')
        hostname = get_hostname()
        # this layer of persisting configuration in sys_store could/should be
        # removed -BLN
        defaults = {'time_zone': "slurp('/etc/timezone').rstrip()",
                    'hostname': "hostname",
                    }
        for k,c in defaults.items():
            if not k in kwargs:
                try:
                    kwargs[k] = sys_store[k]
                except KeyError:
                    exec("if not '%(k)s' in kwargs: sys_store['%(k)s'] = kwargs['%(k)s'] = %(c)s" % {'k':k, 'c':c})
        # over-ride the sys_store cached value
        kwargs['hostname'] = hostname

        ## Get the list of supported timezones and the index in that list of the current one
        module_file = __file__
        if module_file.endswith(".pyc"):
            module_file = module_file[:-1]
        time_zones = json.loads(slurp(os.path.join(os.path.dirname(os.path.realpath(module_file)), "time_zones")))
        for i in range(len(time_zones)):
            if kwargs['time_zone'] == time_zones[i]:
                time_zone_id = i
                break

        ## A little sanity checking.  Make sure the current timezone is in the list.
        try:
            cfg.log('kwargs tz: %s, from_table: %s' % (kwargs['time_zone'], time_zones[time_zone_id]))
        except NameError:
            cfg.log.critical("Unknown Time Zone: %s" % kwargs['time_zone'])
            raise cherrypy.HTTPError(500, "Unknown Time Zone: %s" % kwargs['time_zone'])

        ## And now, the form.
        form = Form(title=_("General Config"),
                        action="/sys/config/general/index",
                        name="config_general_form",
                        message=message )
        form.html(self.help())
        form.dropdown(_("Time Zone"), name="time_zone", vals=time_zones, select=time_zone_id)
        form.html("<p>Your hostname is the local name by which other machines on your LAN can reach you.</p>")
        form.text_input('Hostname', name='hostname', value=kwargs['hostname'])
        form.submit(_("Submit"))
        return form.render()

    def process_form(self, time_zone='', hostname='', *args, **kwargs):
        sys_store = filedict_con(cfg.store_file, 'sys')
        message = ''
        if hostname != sys_store['hostname']:
            msg = valid_hostname(hostname)
            if msg == '':
                old_val = sys_store['hostname']
                try:
                    set_hostname(hostname)
                except Exception, e:
                    cfg.log.error(e)
                    cfg.log.info("Trying to restore old hostname value.")
                    set_hostname(old_val)
                    raise
            else:
                message += msg
        time_zone = time_zone.strip()
        if time_zone != sys_store['time_zone']:
            cfg.log.info("Setting timezone to %s" % time_zone)
            privilegedaction_run("timezone-change", [time_zone])
            sys_store['time_zone'] = time_zone
        return message or "Settings updated."
