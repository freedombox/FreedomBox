# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for samba module."""

import logging
import os
import urllib.parse
from collections import defaultdict

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from plinth import views
from plinth.modules import samba, storage

from . import privileged

logger = logging.getLogger(__name__)


def get_share_mounts():
    """Return list of shareable mounts."""
    ignore_mounts = ('/boot', '/boot/efi', '/boot/firmware', '/.snapshots')
    mounts = []

    for mount in storage.get_mounts():
        mount_point = mount['mount_point']
        if mount_point in ignore_mounts or os.path.isfile(mount_point):
            continue
        basename = os.path.basename(mount_point)
        mount['name'] = basename or _('FreedomBox OS disk')
        mount['share_name_prefix'] = basename or 'disk'
        mounts.append(mount)

    return sorted(mounts, key=lambda k: k['mount_point'])


class SambaAppView(views.AppView):
    """Samba sharing basic configuration."""

    app_id = 'samba'
    template_name = 'samba.html'

    def get_context_data(self, *args, **kwargs):
        """Return template context data."""
        context = super().get_context_data(*args, **kwargs)
        disks = get_share_mounts()
        context['disks'] = disks

        shares = privileged.get_shares()
        shared_mounts = defaultdict(list)
        for share in shares:
            shared_mounts[share['mount_point']].append(share['share_type'])
        context['shared_mounts'] = shared_mounts

        context['share_types'] = [{
            'id': 'open',
            'type': _('Open Share'),
            'share_name_suffix': ''
        }, {
            'id': 'group',
            'type': _('Group Share'),
            'share_name_suffix': '_group'
        }, {
            'id': 'home',
            'type': _('Home Share'),
            'share_name_suffix': '_home'
        }]

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
            except Exception as exception:
                logger.exception('Error enabling share')
                messages.error(
                    request,
                    _('Error enabling share: {error_message}').format(
                        error_message=exception))
        elif action == 'disable':
            try:
                privileged.delete_share(mount_point, share_type)
                messages.success(request, _('Share disabled.'))
            except Exception as exception:
                logger.exception('Error disabling share')
                messages.error(
                    request,
                    _('Error disabling share: {error_message}').format(
                        error_message=exception))

    return redirect(reverse('samba:index'))
