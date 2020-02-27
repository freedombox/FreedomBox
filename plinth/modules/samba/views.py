# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for samba module.
"""

import logging
import urllib.parse
from collections import defaultdict

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from plinth import views
from plinth.errors import ActionError
from plinth.modules import samba, storage

logger = logging.getLogger(__name__)


class SambaAppView(views.AppView):
    """Samba sharing basic configuration."""
    app_id = 'samba'
    template_name = 'samba.html'

    def get_context_data(self, *args, **kwargs):
        """Return template context data."""
        context = super().get_context_data(*args, **kwargs)
        disks = storage.get_disks()
        shares = samba.get_shares()

        for disk in disks:
            disk['name'] = samba.disk_name(disk['mount_point'])
        context['disks'] = disks

        shared_mounts = defaultdict(list)
        for share in shares:
            shared_mounts[share['mount_point']].append(share['share_type'])
        context['shared_mounts'] = shared_mounts

        context['share_types'] = [('open', _('Open Share')),
                                  ('group', _('Group Share')),
                                  ('home', _('Home Share'))]

        unavailable_shares = []
        for share in shares:
            for disk in disks:
                if share['mount_point'] == disk['mount_point']:
                    break
            else:
                unavailable_shares.append(share)
        context['unavailable_shares'] = unavailable_shares

        context['users'] = samba.get_users()

        return context


@require_POST
def share(request, mount_point):
    """Enable sharing, given its root path.

    mount_point is urlquoted.

    """
    mount_point = urllib.parse.unquote(mount_point)
    filesystem = request.POST.get('filesystem_type', '')

    share_types = ['open', 'group', 'home']

    for share_type in share_types:
        action = request.POST.get(share_type + '_share', '')
        if action == 'enable':
            try:
                samba.add_share(mount_point, share_type, filesystem)
                messages.success(request, _('Share enabled.'))
            except ActionError as exception:
                logger.exception('Error enabling share')
                messages.error(
                    request,
                    _('Error enabling share: {error_message}').format(
                        error_message=exception))
        elif action == 'disable':
            try:
                samba.delete_share(mount_point, share_type)
                messages.success(request, _('Share disabled.'))
            except ActionError as exception:
                logger.exception('Error disabling share')
                messages.error(
                    request,
                    _('Error disabling share: {error_message}').format(
                        error_message=exception))

    return redirect(reverse('samba:index'))
