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
Framework for working with servers and their services.
"""

from gettext import gettext as _

import django.dispatch
import collections

from plinth.signals import service_enabled


SERVICES = {}


class Service(object):
    """
    Representation of an application service provided by the machine
    containing information such as current status and ports required
    for operation.
    """

    def __init__(self, service_id, name, ports=None, is_external=False,
                 enabled=True):
        if not ports:
            ports = [service_id]

        self.service_id = service_id
        self.name = name
        self.ports = ports
        self.is_external = is_external
        self._enabled = enabled

        # Maintain a complete list of services
        SERVICES[service_id] = self

    def is_enabled(self):
        """Return whether the service is enabled."""

        if isinstance(self._enabled, collections.Callable):
            return self._enabled()

        return self._enabled

    def notify_enabled(self, sender, enabled):
        """Notify observers about change in state of service."""

        if not isinstance(self._enabled, collections.Callable):
            self._enabled = enabled

        service_enabled.send_robust(sender=sender, service_id=self.service_id,
                            enabled=enabled)


def init():
    """Register some misc. services that don't fit elsewhere."""

    Service('http', _('Web Server'), ['http'], is_external=True, enabled=True)
    Service('https', _('Web Server over Secure Socket Layer'), ['https'],
            is_external=True, enabled=True)
    Service('ssh', _('Secure Shell (SSH) Server'), ['ssh'], is_external=True,
            enabled=True)
    Service('plinth', _('FreedomBox Web Interface (Plinth)'), ['https'],
            is_external=True, enabled=True)
