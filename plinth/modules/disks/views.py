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
