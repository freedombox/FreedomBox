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

from plinth import action_utils, actions

services = {}


class Service():
    """
    Representation of an application service provided by the machine
    containing information such as current status.

    - service_id: unique service name. If possible this should be the name of
                  the service's systemd unit file (without the extension).
    - name: service name as to be displayed in the GUI
    - is_enabled (optional): Boolean or a method returning Boolean
    - enable (optional): method
    - disable (optional): method
    - is_running (optional): Boolean or a method returning Boolean
    """

    def __init__(self, service_id, name, is_enabled=None, enable=None,
                 disable=None, is_running=None):
        if is_enabled is None:
            is_enabled = self._default_is_enabled

        self.service_id = service_id
        self.name = name
        self._is_enabled = is_enabled
        self._enable = enable
        self._disable = disable
        self._is_running = is_running

        # Maintain a complete list of services
        assert service_id not in services
        services[service_id] = self

    def enable(self):
        if self._enable is None:
            actions.superuser_run('service', ['enable', self.service_id])
        else:
            self._call_or_return(self._enable)

    def disable(self):
        if self._disable is None:
            actions.superuser_run('service', ['disable', self.service_id])
        else:
            self._call_or_return(self._disable)

    def is_enabled(self):
        """Return whether the service is enabled."""
        # TODO: we could cache the service state if we only use this service
        # interface to change service status.
        return self._call_or_return(self._is_enabled)

    def is_running(self):
        """Return whether the service is running."""
        if self._is_running is None:
            return action_utils.service_is_running(self.service_id)

        return self._call_or_return(self._is_running)

    @staticmethod
    def _call_or_return(obj):
        """Calls obj if it's callable, returns it if it's Boolean."""
        if isinstance(obj, collections.abc.Callable):
            return obj()

        if isinstance(obj, bool):
            return obj

        message = 'obj is expected to be callable or a boolean.'
        raise ValueError(message)

    def _default_is_enabled(self):
        """Returns is_enabled relying on a correct service_id"""
        return action_utils.service_is_enabled(self.service_id)

    @staticmethod
    def get_internal_interfaces():
        """Returns a list of interfaces in a firewall zone."""
        from plinth.modules import firewall
        return firewall.get_interfaces('internal')
