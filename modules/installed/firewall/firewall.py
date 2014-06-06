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
Plinth module to configure a firewall
"""

import cherrypy
from gettext import gettext as _

import actions
import cfg
from ..lib.auth import require
from plugin_mount import PagePlugin
import service as service_module
import util


class Firewall(PagePlugin):
    """Firewall menu entry and introduction page"""
    order = 40

    def __init__(self, *args, **kwargs):
        PagePlugin.__init__(self, *args, **kwargs)

        self.register_page('sys.firewall')
        cfg.html_root.sys.menu.add_item(_('Firewall'), 'icon-flag',
                                        '/sys/firewall', 50)

        service_module.ENABLED.connect(self.on_service_enabled)

    @cherrypy.expose
    @require()
    def index(self, **kwargs):
        """Serve introcution page"""
        del kwargs  # Unused

        if not self.get_installed_status():
            return util.render_template(template='firewall',
                                        title=_("Firewall"),
                                        firewall_status='not_installed')

        if not self.get_enabled_status():
            return util.render_template(template='firewall',
                                        title=_("Firewall"),
                                        firewall_status='not_running')

        internal_enabled_services = self.get_enabled_services(zone='internal')
        external_enabled_services = self.get_enabled_services(zone='external')

        return util.render_template(
            template='firewall', title=_('Firewall'),
            services=service_module.SERVICES.values(),
            internal_enabled_services=internal_enabled_services,
            external_enabled_services=external_enabled_services)

    def get_installed_status(self):
        """Return whether firewall is installed"""
        output = self._run(['get-installed'], superuser=True)
        return output.split()[0] == 'installed'

    def get_enabled_status(self):
        """Return whether firewall is installed"""
        output = self._run(['get-status'], superuser=True)
        return output.split()[0] == 'running'

    def get_enabled_services(self, zone):
        """Return the status of various services currently enabled"""
        output = self._run(['get-enabled-services', '--zone', zone],
                           superuser=True)
        return output.split()

    def add_service(self, port, zone):
        """Enable a service in firewall"""
        self._run(['add-service', port, '--zone', zone], superuser=True)

    def remove_service(self, port, zone):
        """Remove a service in firewall"""
        self._run(['remove-service', port, '--zone', zone], superuser=True)

    def on_service_enabled(self, sender, service_id, enabled, **kwargs):
        """
        Enable/disable firewall ports when a service is
        enabled/disabled.
        """
        del sender  # Unused
        del kwargs  # Unused

        internal_enabled_services = self.get_enabled_services(zone='internal')
        external_enabled_services = self.get_enabled_services(zone='external')

        cfg.log.info('Service enabled - %s, %s' % (service_id, enabled))
        service = service_module.SERVICES[service_id]
        for port in service.ports:
            if enabled:
                if port not in internal_enabled_services:
                    self.add_service(port, zone='internal')

                if (service.is_external and
                        port not in external_enabled_services):
                    self.add_service(port, zone='external')
                else:
                    # service already configured.
                    pass
            else:
                if port in internal_enabled_services:
                    enabled_services_on_port = [
                        service_.is_enabled()
                        for service_ in service_module.SERVICES.values()
                        if port in service_.ports and
                        service_id != service_.service_id]
                    if not any(enabled_services_on_port):
                        self.remove_service(port, zone='internal')

                if port in external_enabled_services:
                    enabled_services_on_port = [
                        service_.is_enabled()
                        for service_ in service_module.SERVICES.values()
                        if port in service_.ports and
                        service_id != service_.service_id and
                        service_.is_external]
                    if not any(enabled_services_on_port):
                        self.remove_service(port, zone='external')

    @staticmethod
    def _run(arguments, superuser=False):
        """Run an given command and raise exception if there was an error"""
        command = 'firewall'

        cfg.log.info('Running command - %s, %s, %s' % (command, arguments,
                                                       superuser))

        if superuser:
            output, error = actions.superuser_run(command, arguments)
        else:
            output, error = actions.run(command, arguments)

        if error:
            raise Exception('Error setting/getting firewalld confguration - %s'
                            % error)

        return output
