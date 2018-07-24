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

glib = utils.import_from_gi('GLib', '2.0')
udisks = utils.import_from_gi('UDisks', '2.0')


def _get_options():
    """Return the common options used for udisks2 operations."""
    options = glib.Variant(
        'a{sv}', {'auth.no_user_interaction': glib.Variant('b', True)})
    return options


def list_devices():
    """List devices that can be ejected."""
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    block = None
    devices = []
    for obj in object_manager.get_objects():
        if not obj.get_block():
            continue

        block = obj.get_block()
        if block.props.id_usage != 'filesystem' or \
           block.props.hint_system or \
           block.props.read_only:
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


def eject_drive_of_device(device_path):
    """Eject a device after unmounting all of its partitions.

    Return the details (model, vendor) of drives ejected.
    """
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    found_objects = [
        obj for obj in object_manager.get_objects()
        if obj.get_block() and obj.get_block().props.device == device_path
    ]

    if not found_objects:
        raise ValueError(
            _('No such device - {device_path}').format(
                device_path=device_path))

    obj = found_objects[0]

    # Unmount filesystems
    block_device = obj.get_block()
    drive_object_path = block_device.props.drive
    if drive_object_path != '/':
        umount_all_filesystems_of_drive(drive_object_path)
    else:
        # Block device has not associated drive
        umount_filesystem(obj.get_filesystem())

    # Eject the drive
    drive = client.get_drive_for_block(block_device)
    if drive:
        drive.call_eject_sync(_get_options(), None)
        return {
            'vendor': drive.props.vendor,
            'model': drive.props.model,
        }

    return None


def umount_filesystem(filesystem):
    """Unmount a filesystem """
    if filesystem and filesystem.props.mount_points:
        filesystem.call_unmount_sync(_get_options())


def umount_all_filesystems_of_drive(drive_object_path):
    """Unmount all filesystems on block devices of a drive."""
    client = udisks.Client.new_sync()
    object_manager = client.get_object_manager()

    for obj in object_manager.get_objects():
        block_device = obj.get_block()
        if not block_device or block_device.props.drive != drive_object_path:
            continue

        umount_filesystem(obj.get_filesystem())


def get_error_message(error):
    """Return an error message given an exception."""
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
