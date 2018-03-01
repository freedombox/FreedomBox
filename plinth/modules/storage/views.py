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
Views for storage module.
"""

import logging

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _

from plinth.modules import storage
from plinth.utils import format_lazy, is_user_admin

logger = logging.getLogger(__name__)


def index(request):
    """Show connection list."""
    disks = storage.get_disks()
    root_device = storage.get_root_device(disks)
    expandable_root_size = storage.is_expandable(root_device)
    expandable_root_size = storage.format_bytes(expandable_root_size)

    warn_about_low_disk_space(request)

    return TemplateResponse(
        request, 'storage.html', {
            'title': _('Storage'),
            'disks': disks,
            'manual_page': storage.manual_page,
            'expandable_root_size': expandable_root_size
        })


def expand(request):
    """Warn and expand the root partition."""
    disks = storage.get_disks()
    root_device = storage.get_root_device(disks)

    if request.method == 'POST':
        expand_partition(request, root_device)
        return redirect(reverse('storage:index'))

    expandable_root_size = storage.is_expandable(root_device)
    expandable_root_size = storage.format_bytes(expandable_root_size)
    return TemplateResponse(
        request, 'storage_expand.html', {
            'title': _('Expand Root Partition'),
            'expandable_root_size': expandable_root_size
        })


def expand_partition(request, device):
    """Expand the partition."""
    try:
        storage.expand_partition(device)
    except Exception as exception:
        messages.error(request,
                       _('Error expanding partition: {exception}')
                       .format(exception=exception))
    else:
        messages.success(request, _('Partition expanded successfully.'))


def warn_about_low_disk_space(request):
    """Warn about insufficient space on root partition."""
    if not is_user_admin(request, cached=True):
        return

    disks = storage.get_disks()
    list_root = [disk for disk in disks if disk['mountpoint'] == '/']
    if not list_root:
        logger.error('Error getting information about root partition.')
        return

    percent_used = list_root[0]['percent_used']
    size_bytes = list_root[0]['size']
    free_bytes = list_root[0]['free']
    free_gib = free_bytes / (1024**3)

    message = format_lazy(
        # Translators: xgettext:no-python-format
        _('Warning: Low space on system partition ({percent_used}% used, '
          '{free_space} free).'),
        percent_used=percent_used,
        free_space=storage.format_bytes(free_bytes))

    if percent_used > 90 or free_gib < 1:
        messages.error(request, message)
    elif percent_used > 75 or free_gib < 2:
        messages.warning(request, message)
