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
            drive = client.get_drive_for_block(block)
            device['ejectable'] = drive.props.id_type
        except Exception:
            pass

        try:
            device['mount_points'] = obj.get_filesystem().props.mount_points
        except Exception:
            pass

        devices.append(device)

    return devices
