# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for storage module."""

import logging
import urllib.parse

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from plinth import views
from plinth.modules import storage

from . import get_error_message, privileged

logger = logging.getLogger(__name__)


class StorageAppView(views.AppView):
    """Show storage information."""

    app_id = 'storage'
    template_name = 'storage.html'

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
        privileged.expand_partition(device)
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
        drive = privileged.eject(device_path)
        if drive:
            messages.success(
                request,
                _('{drive_vendor} {drive_model} can be safely unplugged.').
                format(drive_vendor=drive['vendor'],
                       drive_model=drive['model']))
        else:
            messages.success(request, _('Device can be safely unplugged.'))
    except Exception as exception:
        message = get_error_message(exception.args[-2].decode())  # stdout

        logger.error('Error ejecting device - %s', message)
        messages.error(
            request,
            _('Error ejecting device: {error_message}').format(
                error_message=message))

    return redirect(reverse('storage:index'))
