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
FreedomBox app for udiskie.
"""

import dbus
from django.utils.translation import ugettext_lazy as _

from plinth import service as service_module
from plinth import action_utils, actions
from plinth.menu import main_menu
from plinth.modules.storage import format_bytes

version = 1

managed_services = ['freedombox-udiskie']

managed_packages = ['udiskie']

name = _('udiskie')

short_description = _('Removable Media')

description = [
    _('udiskie allows automatic mounting of removable media, such as flash '
      'drives.'),
]

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('system')
    menu.add_urlname(name, 'glyphicon-floppy-disk', 'udiskie:index',
                     short_description)

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], name, ports=[], is_external=False,
            is_enabled=is_enabled, enable=enable, disable=disable,
            is_running=is_running)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages, skip_recommends=True)
    helper.call('post', actions.superuser_run, 'udiskie', ['enable'])
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], name, ports=[], is_external=True,
            is_enabled=is_enabled, enable=enable, disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running('freedombox-udiskie')


def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.service_is_enabled('freedombox-udiskie')


def enable():
    """Enable the module."""
    actions.superuser_run('udiskie', ['enable'])


def disable():
    """Disable the module."""
    actions.superuser_run('udiskie', ['disable'])


def list_devices():
    UDISKS2 = 'org.freedesktop.UDisks2'
    UDISKS2_PATH = '/org/freedesktop/UDisks2'
    BLOCK = UDISKS2 + '.Block'
    PROPERTIES = 'org.freedesktop.DBus.Properties'

    devices = []
    bus = dbus.SystemBus()
    udisks_obj = bus.get_object(UDISKS2, UDISKS2_PATH)
    manager = dbus.Interface(udisks_obj, 'org.freedesktop.DBus.ObjectManager')
    for k, v in manager.GetManagedObjects().items():
        drive_info = v.get(BLOCK, {})
        if drive_info.get('IdUsage') == "filesystem" \
           and not drive_info.get('HintSystem') \
           and not drive_info.get('ReadOnly'):
            device_name = drive_info.get('Device')
            if device_name:
                device_name = bytearray(device_name).replace(
                    b'\x00', b'').decode('utf-8')
                short_name = device_name.replace('/dev', '', 1)
                bd = bus.get_object(
                    UDISKS2, UDISKS2_PATH + '/block_devices%s' % short_name)
                drive_name = bd.Get(BLOCK, 'Drive', dbus_interface=PROPERTIES)
                drive = bus.get_object(UDISKS2, drive_name)
                ejectable = drive.Get(UDISKS2 + '.Drive', 'Ejectable',
                                      dbus_interface=PROPERTIES)
                if ejectable:
                    label = bd.Get(BLOCK, 'IdLabel', dbus_interface=PROPERTIES)
                    size = bd.Get(BLOCK, 'Size', dbus_interface=PROPERTIES)
                    file_system = bd.Get(BLOCK, 'IdType',
                                         dbus_interface=PROPERTIES)
                    try:
                        mount_points = bd.Get(UDISKS2 + '.Filesystem',
                                              'MountPoints',
                                              dbus_interface=PROPERTIES)
                        mount_point = mount_points[0]
                    except:
                        mount_point = None

                    devices.append({
                        'device':
                            device_name,
                        'label':
                            str(label),
                        'size':
                            format_bytes(size),
                        'file_system':
                            str(file_system),
                        'mount_point':
                            ''.join([chr(ch) for ch in mount_point]),
                    })

    return devices
