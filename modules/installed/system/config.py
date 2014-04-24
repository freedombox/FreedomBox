#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Plinth module for configuring timezone, hostname etc.
"""

import cherrypy
from gettext import gettext as _
try:
    import simplejson as json
except ImportError:
    import json
import os
import socket

import actions
import cfg
from forms import Form
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import util


class Config(PagePlugin):
    """System configuration page"""
    def __init__(self, *args, **kwargs):
        del args  # Unused
        del kwargs  # Unused

        self.register_page("sys.config")

    @cherrypy.expose
    @require()
    def index(self):
        """Serve configuration page"""
        parts = self.forms('/sys/config')
        parts['title'] = _("Configure this {box_name}") \
            .format(box_name=cfg.box_name)

        return self.fill_template(**parts)  # pylint: disable-msg=W0142


def valid_hostname(name):
    """
    Return '' if name is a valid hostname by our standards (not just
    by RFC 952 and RFC 1123.  We're more conservative than the
    standard.  If hostname isn't valid, return message explaining why.
    """
    message = ''
    if len(name) > 63:
        message += "<br />Hostname too long (max is 63 characters)"

    if not util.is_alphanumeric(name):
        message += "<br />Hostname must be alphanumeric"

    if not name[0] in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ":
        message += "<br />Hostname must start with a letter"

    return message


def get_hostname():
    """Return the current hostname of the system"""
    return socket.gethostname()


def get_time_zone():
    """Return currently set system's timezone"""
    return util.slurp('/etc/timezone').rstrip()


def set_hostname(hostname):
    """Sets machine hostname to hostname"""
    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert to ASCII.
    hostname = str(hostname)

    cfg.log.info("Changing hostname to '%s'" % hostname)
    try:
        actions.superuser_run("xmpp-pre-hostname-change")
        actions.superuser_run("hostname-change", hostname)
        actions.superuser_run("xmpp-hostname-change", hostname, async=True)
        # don't persist/cache change unless it was saved successfuly
        sys_store = util.filedict_con(cfg.store_file, 'sys')
        sys_store['hostname'] = hostname
    except OSError as exception:
        raise cherrypy.HTTPError(500,
                                 'Updating hostname failed: %s' % exception)

class general(FormPlugin, PagePlugin):
    """Form to update hostname and time zone"""
    url = ["/sys/config"]
    order = 30

    @staticmethod
    def help(*args, **kwargs):
        """Build and return the help content area"""
        del args  # Unused
        del kwargs  # Unused

        return _('''
<p>Set your timezone to get accurate timestamps.  {product} will use
this information to set your {box}'s systemwide timezone.</p>''').format(
            product=cfg.product_name, box=cfg.box_name)

    def main(self, message='', time_zone=None, **kwargs):
        """Build and return the main content area which is the form"""
        del kwargs  # Unused

        if not cfg.users.expert():
            return _('''
<p>Only members of the expert group are allowed to see and modify the system
setup.</p>''')

        if not time_zone:
            time_zone = get_time_zone()

        # Get the list of supported timezones and the index in that
        # list of the current one
        module_file = __file__
        if module_file.endswith(".pyc"):
            module_file = module_file[:-1]
        module_dir = os.path.dirname(os.path.realpath(module_file))
        time_zones_file = os.path.join(module_dir, 'time_zones')
        time_zones = json.loads(util.slurp(time_zones_file))
        try:
            time_zone_id = time_zones.index(time_zone)
        except ValueError:
            cfg.log.critical("Unknown Time Zone: %s" % time_zone)
            raise cherrypy.HTTPError(500, "Unknown Time Zone: %s" % time_zone)

        # And now, the form.
        form = Form(title=_("General Config"),
                    action=cfg.server_dir + "/sys/config/general/index",
                    name="config_general_form",
                    message=message)
        form.html(self.help())
        form.dropdown(_("Time Zone"), name="time_zone", vals=time_zones,
                      select=time_zone_id)
        form.html('''
<p>Your hostname is the local name by which other machines on your LAN
can reach you.</p>''')
        form.text_input('Hostname', name='hostname', value=get_hostname())
        form.submit(_("Submit"))

        return form.render()

    @staticmethod
    def process_form(time_zone='', hostname='', *args, **kwargs):
        """Handle form submission"""
        del args  # Unused
        del kwargs  # Unused

        message = ''
        if hostname != get_hostname():
            msg = valid_hostname(hostname)
            if msg == '':
                set_hostname(hostname)
            else:
                message += msg

        time_zone = time_zone.strip()
        if time_zone != get_time_zone():
            cfg.log.info("Setting timezone to %s" % time_zone)
            actions.superuser_run("timezone-change", [time_zone])

        return message or "Settings updated."
