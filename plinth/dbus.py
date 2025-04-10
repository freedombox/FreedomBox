# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Expose some API over D-Bus.
"""

import logging
import threading

from plinth.utils import import_from_gi

from . import setup

gio = import_from_gi('Gio', '2.0')

logger = logging.getLogger(__name__)

_server = None


class PackageHandler():
    """D-Bus service to listen for messages when apt cache is updated."""

    introspection_xml = '''
<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE node PUBLIC "-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
  "http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
<node name="/org/freedombox/Service/PackageHandler">
  <interface name="org.freedombox.Service.PackageHandler">
    <method name="CacheUpdated"/>
    <method name="DpkgInvoked"/>
  </interface>
</node>
'''

    def register(self, connection):
        """Register the object in D-Bus connection."""
        introspection_data = gio.DBusNodeInfo.new_for_xml(
            self.introspection_xml)
        interface_info = gio.DBusNodeInfo.lookup_interface(
            introspection_data, 'org.freedombox.Service.PackageHandler')
        connection.register_object('/org/freedombox/Service/PackageHandler',
                                   interface_info, self.on_method_call, None,
                                   None)

    def on_method_call(self, _connection, _sender, _object_path,
                       _interface_name, method_name, _parameters, invocation):
        """Handle method being called.

        No need to check all the incoming parameters as D-Bus will validate all
        the incoming parameters using introspection data.
        """
        if method_name == 'CacheUpdated':
            self.on_cache_updated()
            invocation.return_value()

        if method_name == 'DpkgInvoked':
            self.on_dpkg_invoked()
            invocation.return_value()

    @staticmethod
    def on_cache_updated():
        """Called when system package cache is updated."""
        logger.info('Apt package cache updated.')

        # Run in a new thread because we don't want to block the thread running
        # Glib main loop.
        threading.Thread(target=setup.on_package_cache_updated).start()

    @staticmethod
    def on_dpkg_invoked():
        """Called when dpkg has been invoked."""
        logger.info('Dpkg invoked outside of FreedomBox.')

        # Run in a new thread because we don't want to block the thread running
        # Glib main loop.
        threading.Thread(target=setup.on_dpkg_invoked).start()


class DBusServer():
    """Abstraction over a connection to D-Bus."""

    def __init__(self):
        """Initialize the server object."""
        self.package_handler = None

    def connect(self):
        """Connect to bus with well-known name."""
        gio.bus_own_name(gio.BusType.SYSTEM, 'org.freedombox.Service',
                         gio.BusNameOwnerFlags.NONE, self.on_bus_acquired,
                         self.on_name_acquired, self.on_name_lost)

    def on_bus_acquired(self, connection, name):
        """Callback when connection to D-Bus has been acquired."""
        logger.info('D-Bus connection acquired: %s', name)
        self.package_handler = PackageHandler()
        self.package_handler.register(connection)

        from plinth.modules.letsencrypt.dbus import LetsEncrypt
        lets_encrypt = LetsEncrypt()
        lets_encrypt.register(connection)

    @staticmethod
    def on_name_acquired(_connection, name):
        """Callback when service name on D-Bus has been acquired."""
        logger.info('D-Bus name acquired: %s', name)

    @staticmethod
    def on_name_lost(_connection, name):
        """Callback when service name or DBus connection is closed."""
        logger.info('D-Bus connection lost: %s', name)

        # XXX: Reconnect after a while
        #
        # Such as by doing:
        # connection.set_exit_on_close(False)
        # gio.timeout_add(10000, self.connect)
        #
        # However, perhaps due to some cleanup issues, reconnection is not
        # happening if it is does after an incoming method call.
        #
        # If D-Bus connection is lost due to daemon restart, FreedomBox service
        # will receive a SIGTERM and exit. systemd should then restart the
        # service again.


def init():
    """Connect to D-Bus service. Must be run from glib thread."""
    global _server
    _server = DBusServer()
    _server.connect()
