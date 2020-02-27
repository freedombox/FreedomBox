# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Expose API over D-Bus to receive renewal notifications.
"""

import logging

from plinth.utils import import_from_gi

gio = import_from_gi('Gio', '2.0')

logger = logging.getLogger(__name__)


class LetsEncrypt:
    """D-Bus service to listen for Let's Encrypt renewal notifications."""

    introspection_xml = '''
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node name="/org/freedombox/Service/LetsEncrypt">
  <interface name="org.freedombox.Service.LetsEncrypt">
    <method name="DeployHook">
      <arg name="renewed_domains" type="s" direction="in"/>
      <arg name="renewed_lineage" type="s" direction="in"/>
    </method>
  </interface>
</node>
'''

    def register(self, connection):
        """Register the object in D-Bus connection."""
        introspection_data = gio.DBusNodeInfo.new_for_xml(
            self.introspection_xml)
        interface_info = gio.DBusNodeInfo.lookup_interface(
            introspection_data, 'org.freedombox.Service.LetsEncrypt')
        connection.register_object('/org/freedombox/Service/LetsEncrypt',
                                   interface_info, self.on_method_call, None,
                                   None)

    def on_method_call(self, _connection, _sender, _object_path,
                       _interface_name, method_name, parameters, invocation):
        """Handle method being called.

        No need to check all the incoming parameters as D-Bus will validate all
        the incoming parameters using introspection data.

        """
        if method_name == 'DeployHook':
            self._on_deploy_hook(parameters[0], parameters[1])
            invocation.return_value()

    @staticmethod
    def _on_deploy_hook(renewed_domains, renewed_lineage):
        """Run renewal hooks for each app.

        Don't run this a new thread here because
        component.on_certificate_event() creates one anyway.

        """
        logger.info('LE certificate renewed (deployed): %s, %s.',
                    renewed_domains, renewed_lineage)

        from plinth.modules.letsencrypt import components
        components.on_certificate_event('renewed', renewed_domains,
                                        renewed_lineage)
