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
Plinth module for configuring PageKite service
"""

import cherrypy
from gettext import gettext as _

import actions
import cfg
from forms import Form
from modules.auth import require
from plugin_mount import PagePlugin, FormPlugin
import re
import util


class PageKite(PagePlugin):
    """PageKite menu entry and introduction page"""
    order = 60

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page("router.setup.pagekite")
        self.register_page("router.setup.pagekite.configure")
        cfg.html_root.router.setup.menu.add_item(
            _("Public Visibility (PageKite)"), "icon-flag",
            "/router/setup/pagekite", 50)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve introcution page"""
        del kwargs  # Unused

        main = _("""
<p>PageKite is a system for exposing {box_name} services when you
don't have a direct connection to the Internet. You only need this
service if your {box_name} services are unreachable from the rest of
the Internet. This includes the following situations: </p>

<ul>
  <li>{box_name} is behind a restricted firewall.</li>

  <li>{box_name} is connected to a (wireless) router which you don't
      control.</li>

  <li>Your ISP does not provide you an external IP address and instead
      provides Internet connection through NAT.</li>

  <li>Your ISP does not provide you a static IP address and your IP
      address changes evertime you connect to Internet.</li>

  <li>Your ISP limits incoming connections.</li>
</ul>

<p>PageKite works around NAT, firewalls and IP-address limitations by
using a combination of tunnels and reverse proxies. Currently,
exposing web server and SSH server are supported. An intermediary
server with direct Internet access is required. Currently, only
pagekite.net server is supported and you will need an account
there. In future, it might be possible to use your buddy's {box_name}
for this.</p>

<p><a class='btn btn-primary btn-lg'
      href="{server_dir}/router/setup/pagekite/configure">Configure
PageKite</a></p>
""").format(box_name=cfg.box_name, server_dir=cfg.server_dir)

        sidebar_right = _('''
<strong>PageKite</strong>
<p><a href="{server_dir}/router/setup/pagekite/configure">Configure
PageKite</a> </p>''').format(server_dir=cfg.server_dir)

        return self.fill_template(title=_("Public Visibility (PageKite)"),
                                  main=main, sidebar_right=sidebar_right)


class configure(FormPlugin, PagePlugin):  # pylint: disable-msg=C0103
    """Main configuration form"""
    order = 65

    url = ["/router/setup/pagekite/configure"]

    js = """
<script type="text/javascript">
(function($) {

$('#pagekite-server').attr("disabled", "disabled");

$('#pagekite-enable').change(function() {
    if ($('#pagekite-enable').prop('checked')) {
        $('#pagekite-post-enable-form').show('slow');
    } else {
        $('#pagekite-post-enable-form').hide('slow');
    }
});

})(jQuery);
</script>
"""

    def get_status(self):
        """
        Return the current status of PageKite configuration by
        executing various actions.
        """
        status = {}

        # Check if PageKite is installed
        output = self._run(['get-installed'])
        cfg.log('Output - %s' % output)
        if output.split()[0] != 'installed':
            return None

        # PageKite service enabled/disabled
        output = self._run(['get-status'])
        status['enabled'] = (output.split()[0] == 'enabled')

        # PageKite kite details
        output = self._run(['get-kite'])
        kite_details = output.split()
        status['kite_name'] = kite_details[0]
        status['kite_secret'] = kite_details[1]

        # Service status
        status['service'] = {}
        for service in ('http', 'ssh'):
            output = self._run(['get-service-status', service])
            status['service'][service] = (output.split()[0] == 'enabled')

        return status

    def main(self, *args, **kwargs):
        """Build and return the main content area which is the form"""
        del args  # unused

        status = self.get_status()

        if not status:
            return _('''
<p>PageKite is not installed, please install it. PageKite comes
pre-installed with {box_name}. On any Debian based system (such as
{box_name}) you may install it using the command 'aptitude install
pagekite'</p>''').format(box_name=cfg.box_name)

        try:
            message = kwargs['message'].text
        except KeyError:
            message = None
        form = Form(
            title="Configure PageKite",
            action=cfg.server_dir + "/router/setup/pagekite/configure/",
            name="configure_pagekite_form", message=message)

        form.checkbox(_("Enable PageKite"), name="pagekite_enable",
                      id="pagekite-enable", checked=status['enabled'])

        show_form = "block" if status['enabled'] else "none"
        form.html('''
<div id='pagekite-post-enable-form'
     style='display: {show_form}'>'''.format(show_form=show_form))

        form.html(_("<h3>PageKite Account</h3>"))
        form.text_input(_("Server"), name="pagekite_server",
                        id="pagekite-server", value="pagekite.net")
        form.text_input(_("Kite name"), name="pagekite_kite_name",
                        id="pagekite-kite-name", value=status['kite_name'])
        form.text_input(_("Kite secret"), name="pagekite_kite_secret",
                        id="pagekite-kite-secret", value=status['kite_secret'])

        form.html(_("<h3>Services</h3>"))
        form.checkbox(_("Web Server (HTTP)"), name="pagekite_http_enable",
                      id="pagekite-http-enable",
                      checked=status['service']['http'])
        form.checkbox(_("Secure Shell (SSH)"), name="pagekite_ssh_enable",
                      id="pagekite-ssh-enable",
                      checked=status['service']['ssh'])

        form.html("</div>")  # pagekite-post-enable-form

        form.submit(_("Update setup"))
        return form.render()

    def process_form(self, **kwargs):
        """Handle form submission"""
        status = self.get_status()

        message, new_status = self.validate_form(**kwargs)
        if not message.text:
            self.apply_changes(status, new_status, message)

        return message

    @staticmethod
    def validate_form(**kwargs):
        """Check whether all the input form values are correct"""
        new_status = {}
        message = util.Message()

        domain_name_re = r'^[\w-]{1,63}(\.[\w-]{1,63})*$'
        pagekite_kite_name = kwargs.get('pagekite_kite_name', '').strip()
        if not re.match(domain_name_re, pagekite_kite_name):
            message.add(_('Invalid kite name'))
        else:
            new_status['kite_name'] = pagekite_kite_name

        pagekite_kite_secret = kwargs.get('pagekite_kite_secret', '').strip()
        if not pagekite_kite_secret:
            message.add(_('Invalid kite secret'))
        else:
            new_status['kite_secret'] = pagekite_kite_secret

        new_status['enabled'] = (kwargs.get('pagekite_enable') == 'on')
        new_status['service'] = {
            'http': (kwargs.get('pagekite_http_enable') == 'on'),
            'ssh': (kwargs.get('pagekite_ssh_enable') == 'on')
            }

        return message, new_status

    def apply_changes(self, old_status, new_status, message):
        """Apply the changes to PageKite configuration"""
        cfg.log.info('New status is - %s' % new_status)

        if old_status != new_status:
            self._run(['stop'])

        if old_status['enabled'] != new_status['enabled']:
            if new_status['enabled']:
                self._run(['set-status', 'enable'])
                message.add(_('PageKite enabled'))
            else:
                self._run(['set-status', 'disable'])
                message.add(_('PageKite disabled'))

        if old_status['kite_name'] != new_status['kite_name'] or \
                old_status['kite_secret'] != new_status['kite_secret']:
            self._run(['set-kite', '--kite-name', new_status['kite_name'],
                       '--kite-secret', new_status['kite_secret']])
            message.add(_('Kite details set'))

        for service, old_value in old_status['service'].items():
            if old_value != new_status['service'][service]:
                if new_status['service'][service]:
                    self._run(['set-service-status', service, 'enable'])
                    message.add(_('Service enabled: {service}')
                                .format(service=service))
                else:
                    self._run(['set-service-status', service, 'disable'])
                    message.add(_('Service disabled: {service}')
                                .format(service=service))

        if old_status != new_status:
            self._run(['start'])

    @staticmethod
    def _run(arguments, superuser=True):
        """Run an given command and raise exception if there was an error"""
        command = 'pagekite-configure'

        cfg.log.info('Running command - %s, %s, %s' % (command, arguments,
                                                       superuser))

        if superuser:
            output, error = actions.superuser_run(command, arguments)
        else:
            output, error = actions.run(command, arguments)

        if error:
            raise Exception('Error setting/getting PageKite confguration - %s'
                            % error)

        return output
