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

import logging
from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
from plinth.modules import disks as disks_module
from plinth.utils import format_lazy, is_user_admin


logger = logging.getLogger(__name__)


def index(request):
    """Show connection list."""
    disks = disks_module.get_disks()
    root_device = disks_module.get_root_device(disks)
    expandable_root_size = disks_module.is_expandable(root_device)
    expandable_root_size = _format_bytes(expandable_root_size)

    warn_about_low_disk_space(request)

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


def warn_about_low_disk_space(request):
    """Warn about insufficient space on root partition."""
    if not is_user_admin(request, cached=True):
        return

    disks = disks_module.get_disks()
    list_root = [disk for disk in disks if disk['mountpoint'] == '/']
    if not list_root:
        logger.error('Error getting information about root partition.')
        return

    perc_used = list_root[0]['percentage_used']
    size_bytes = _interpret_size_string(list_root[0]['size'])
    free_bytes = size_bytes * (100 - perc_used) / 100

    message = format_lazy(
        _('Warning: Low space on system partition ({percent_used}% used, '
          '{free_space} free).'),
        percent_used=perc_used, free_space=_format_bytes(free_bytes))

    free_gib = free_bytes / (1024 ** 3)
    if perc_used > 90 or free_gib < 1:
        messages.error(request, message)
    elif perc_used > 75 or free_gib < 2:
        messages.warning(request, message)


def _interpret_size_string(size_str):
    """Convert size string to number of bytes."""
    if size_str[-1] in '0123456789':
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
