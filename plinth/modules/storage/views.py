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

import json
import logging
import urllib.parse

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import actions, views
from plinth.modules import storage

from . import get_error_message

logger = logging.getLogger(__name__)


class StorageAppView(views.AppView):
    """Show storage information."""
    name = storage.name
    description = storage.description
    manual_page = storage.manual_page
    app_id = 'storage'
    template_name = 'storage.html'
    show_status_block = False

    def get_context_data(self, *args, **kwargs):
        """Return template context data."""
        context = super().get_context_data(*args, **kwargs)

        disks = storage.get_disks()
        root_device = storage.get_root_device(disks)
        expandable_root_size = storage.is_expandable(root_device)
        expandable_root_size = storage.format_bytes(expandable_root_size)

        context['disks'] = disks
        context['expandable_root_size'] = expandable_root_size
        return context


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
        messages.error(
            request,
            _('Error expanding partition: {exception}').format(
                exception=exception))
    else:
        messages.success(request, _('Partition expanded successfully.'))


@require_POST
def eject(request, device_path):
    """Eject a device, given its path.

    Device path is quoted with slashes written as %2F.

    """
    device_path = urllib.parse.unquote(device_path)

    try:
        drive = json.loads(
            actions.superuser_run('storage', ['eject', device_path]))
        if drive:
            messages.success(
                request,
                _('{drive_vendor} {drive_model} can be safely unplugged.').
                format(drive_vendor=drive['vendor'],
                       drive_model=drive['model']))
        else:
            messages.success(request, _('Device can be safely unplugged.'))
    except Exception as exception:
        try:
            message = get_error_message(exception)
        except AttributeError:
            message = str(exception)

        logger.exception('Error ejecting device - %s', message)
        messages.error(
            request,
            _('Error ejecting device: {error_message}').format(
                error_message=message))

    return redirect(reverse('storage:index'))
