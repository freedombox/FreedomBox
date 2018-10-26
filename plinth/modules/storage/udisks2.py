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
Library for interacting with udisks2 D-Bus service.
"""

from django.utils.translation import ugettext as _

from plinth import utils
from plinth.modules.storage import format_bytes


def list_devices():
    """List devices that can be ejected."""
    udisks = utils.import_from_gi('UDisks', '2.0')
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    block = None
    devices = []
    for obj in object_manager.get_objects():
        if not obj.get_block():
            continue

        block = obj.get_block()
        if block.props.id_usage != 'filesystem' or \
           block.props.hint_system:
            continue

        device_name = block.props.device
        if not device_name:
            continue

        device = {
            'device': block.props.device,
            'label': block.props.id_label,
            'size': format_bytes(block.props.size),
            'filesystem_type': block.props.id_type
        }

        try:
            device['mount_points'] = obj.get_filesystem().props.mount_points
        except Exception:
            pass

        devices.append(device)

    return devices


def get_error_message(error):
    """Return an error message given an exception."""
    udisks = utils.import_from_gi('UDisks', '2.0')
    if error.matches(udisks.Error.quark(), udisks.Error.FAILED):
        message = _('The operation failed.')
    elif error.matches(udisks.Error.quark(), udisks.Error.CANCELLED):
        message = _('The operation was cancelled.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_UNMOUNTING):
        message = _('The device is already unmounting.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_SUPPORTED):
        message = _('The operation is not supported due to '
                    'missing driver/tool support.')
    elif error.matches(udisks.Error.quark(), udisks.Error.TIMED_OUT):
        message = _('The operation timed out.')
    elif error.matches(udisks.Error.quark(), udisks.Error.WOULD_WAKEUP):
        message = _('The operation would wake up a disk that is '
                    'in a deep-sleep state.')
    elif error.matches(udisks.Error.quark(), udisks.Error.DEVICE_BUSY):
        message = _('Attempting to unmount a device that is busy.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_CANCELLED):
        message = _('The operation has already been cancelled.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_AUTHORIZED) or \
        error.matches(udisks.Error.quark(),
                      udisks.Error.NOT_AUTHORIZED_CAN_OBTAIN) or \
        error.matches(udisks.Error.quark(),
                      udisks.Error.NOT_AUTHORIZED_DISMISSED):
        message = _('Not authorized to perform the requested operation.')
    elif error.matches(udisks.Error.quark(), udisks.Error.ALREADY_MOUNTED):
        message = _('The device is already mounted.')
    elif error.matches(udisks.Error.quark(), udisks.Error.NOT_MOUNTED):
        message = _('The device is not mounted.')
    elif error.matches(udisks.Error.quark(),
                       udisks.Error.OPTION_NOT_PERMITTED):
        message = _('Not permitted to use the requested option.')
    elif error.matches(udisks.Error.quark(),
                       udisks.Error.MOUNTED_BY_OTHER_USER):
        message = _('The device is mounted by another user.')
    else:
        message = error.message

    return message
