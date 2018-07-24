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
Views for udiskie module.
"""

import urllib.parse
from logging import Logger

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth.views import ServiceView

from . import udisks2

logger = Logger(__name__)


class Index(ServiceView):
    """View to show devices."""
    template_name = 'udiskie.html'

    def get_context_data(self, *args, **kwargs):
        """Return the context data rendering the template."""
        context = super().get_context_data(**kwargs)
        context['devices'] = udisks2.list_devices()
        return context


@require_POST
def eject(request, device_path):
    """Eject a device, given its path.

    Device path is quoted with slashes written as %2F.

    """
    device_path = urllib.parse.unquote(device_path)

    try:
        drive = udisks2.eject_drive_of_device(device_path)
        if drive:
            messages.success(
                request,
                _('{drive_vendor} {drive_model} can be safely unplugged.')
                .format(drive_vendor=drive['vendor'],
                        drive_model=drive['model']))
        else:
            messages.success(request, _('Device can be safely unplugged.'))
    except Exception as exception:
        try:
            message = udisks2.get_error_message(exception)
        except AttributeError:
            message = str(exception)

        logger.exception('Error ejecting device - %s', message)
        messages.error(
            request,
            _('Error ejecting device: {error_message}').format(
                error_message=message))

    return redirect(reverse('udiskie:index'))
