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
Views for disks module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _

from plinth.modules import disks as disks_module


def index(request):
    """Show connection list."""
    disks = disks_module.get_disks()
    root_device = disks_module.get_root_device(disks)
    expandable_root_size = disks_module.is_expandable(root_device)
    expandable_root_size = _format_bytes(expandable_root_size)

    return TemplateResponse(request, 'disks.html',
                            {'title': _('Disks'),
                             'disks': disks,
                             'expandable_root_size': expandable_root_size})


def expand(request):
    """Warn and expand the root partition."""
    disks = disks_module.get_disks()
    root_device = disks_module.get_root_device(disks)

    if request.method == 'POST':
        expand_partition(request, root_device)
        return redirect(reverse('disks:index'))

    expandable_root_size = disks_module.is_expandable(root_device)
    expandable_root_size = _format_bytes(expandable_root_size)
    return TemplateResponse(request, 'disks_expand.html',
                            {'title': _('Expand Root Partition'),
                             'expandable_root_size': expandable_root_size})


def expand_partition(request, device):
    """Expand the partition."""
    try:
        disks_module.expand_partition(device)
    except Exception as exception:
        messages.error(request, _('Error expanding partition: {exception}')
                       .format(exception=exception))
    else:
        messages.success(request, _('Partition expanded successfully.'))


def warn_about_insufficient_root_space(request):
    """Warn about insufficient space on root partition."""
    disks = disks_module.get_disks()
    list_root = [disk for disk in disks if disk['mountpoint'] == '/']
    perc_used = list_root[0]['percentage_used'] if list_root else -1
    size_str = list_root[0]['size'] if list_root else '-1'
    size_Bytes = _interpret_size_string(size_str)
    free_Bytes = size_Bytes * (100 - perc_used) / 100
    free_GiB = free_Bytes / 1024 ** 3
    free_str = _format_bytes(free_Bytes)

    if perc_used < 0 or free_GiB < 0:
        # FIXME: Log read error.
        return

    msg_str = _('Warning: Low disk space on root partition ({percent_used}%'
                ' used, {free_space} free). FIXME: Link to disk module.').format(
                    percent_used=perc_used, free_space=free_str)

    # FIXME: Match with existing coloring in disk module.
    if perc_used > 90 or free_GiB < 3:
        messages.error(request, msg_str)

    elif perc_used > 80 or free_GiB < 2:
        messages.warning(request, msg_str)


def _interpret_size_string(size_str):
    """Convert size string to number of bytes."""
    if size_str is None or not size_str:
        return -1

    if size_str[-1] in '-10123456789':
        return float(size_str[:-1])

    if size_str[-1] == 'K':
        return float(size_str[:-1]) * 1024

    if size_str[-1] == 'M':
        return float(size_str[:-1]) * 1024 ** 2

    if size_str[-1] == 'G':
        return float(size_str[:-1]) * 1024 ** 3

    if size_str[-1] == 'T':
        return float(size_str[:-1]) * 1024 ** 4

    return -1


def _format_bytes(size):
    """Return human readable disk size from bytes."""
    if not size:
        return size

    if size < 1024:
        return _('{disk_size:.1f} bytes').format(disk_size=size)

    if size < 1024 ** 2:
        size /= 1024
        return _('{disk_size:.1f} KiB').format(disk_size=size)

    if size < 1024 ** 3:
        size /= 1024 ** 2
        return _('{disk_size:.1f} MiB').format(disk_size=size)

    if size < 1024 ** 4:
        size /= 1024 ** 3
        return _('{disk_size:.1f} GiB').format(disk_size=size)

    size /= 1024 ** 4
    return _('{disk_size:.1f} TiB').format(disk_size=size)
