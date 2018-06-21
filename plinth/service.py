#
# This file is part of FreedomBox.
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
Framework for working with servers and their services.
"""

import collections

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions, cfg
from plinth.signals import service_enabled
from plinth.utils import format_lazy

services = {}


class Service(object):
    """
    Representation of an application service provided by the machine
    containing information such as current status and ports required
    for operation.

    - service_id: unique service name. If possible this should be the name of
                  the service's systemd unit file (without the extension).
    - name: service name as to be displayed in the GUI
    - is_enabled (optional): Boolean or a method returning Boolean
    - enable (optional): method
    - disable (optional): method
    - is_running (optional): Boolean or a method returning Boolean
    """
    def __init__(self, service_id, name, ports=None, is_external=False,
                 is_enabled=None, enable=None, disable=None, is_running=None):
        if ports is None:
            ports = []

        if is_enabled is None:
            is_enabled = self._default_is_enabled

        self.service_id = service_id
        self.name = name
        self.ports = ports
        self.is_external = is_external
        self._is_enabled = is_enabled
        self._enable = enable
        self._disable = disable
        self._is_running = is_running

        # Maintain a complete list of services
        assert(service_id not in services)
        services[service_id] = self

    def enable(self):
        if self._enable is None:
            actions.superuser_run('service', ['enable', self.service_id])
        else:
            self._call_or_return(self._enable)
        self.notify_enabled(None, True)

    def disable(self):
        if self._disable is None:
            actions.superuser_run('service', ['disable', self.service_id])
        else:
            self._call_or_return(self._disable)
        self.notify_enabled(None, False)

    def is_enabled(self):
        """Return whether the service is enabled."""
        # TODO: we could cache the service state if we only use this service
        # interface to change service status.
        return self._call_or_return(self._is_enabled)

    def is_running(self):
        if self._is_running is None:
            return action_utils.service_is_running(self.service_id)
        else:
            return self._call_or_return(self._is_running)

    def notify_enabled(self, sender, enabled):
        """Notify observers about change in state of service."""
        service_enabled.send_robust(sender=sender, service_id=self.service_id,
                                    enabled=enabled)

    def _call_or_return(self, obj):
        """Calls obj if it's callable, returns it if it's Boolean."""
        if isinstance(obj, collections.Callable):
            return obj()
        elif type(obj) is bool:
            return obj
        else:
            message = 'obj is expected to be callable or a boolean.'
            raise ValueError(message)

    def _default_is_enabled(self):
        """Returns is_enabled relying on a correct service_id"""
        return action_utils.service_is_enabled(self.service_id)

    def get_internal_interfaces(self):
        """Returns a list of interfaces in a firewall zone."""
        from plinth.modules import firewall
        return firewall.get_interfaces('internal')


def init():
    """Register some misc. services that don't fit elsewhere."""
    Service('http', _('Web Server'), ports=['http'], is_external=True,
            is_enabled=True)
    Service('https', _('Web Server over Secure Socket Layer'), ports=['https'],
            is_external=True, is_enabled=True)
    Service('plinth', format_lazy(_('{box_name} Web Interface (Plinth)'),
                                  box_name=_(cfg.box_name)),
            ports=['https'], is_external=True, is_enabled=True)
