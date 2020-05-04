# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for snapshot module.
"""

import json

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

from plinth import actions
from plinth.errors import ActionError
from plinth.modules import snapshot as snapshot_module
from plinth.modules import storage

from . import get_configuration
from .forms import SnapshotForm

subsubmenu = [
    {
        'url': reverse_lazy('snapshot:index'),
        'text': ugettext_lazy('Configure')
    },
    {
        'url': reverse_lazy('snapshot:manage'),
        'text': ugettext_lazy('Manage Snapshots')
    },
]


def not_supported_view(request):
    """Show that snapshots are not supported on the system."""
    template_data = {
        'app_info': snapshot_module.app.info,
        'title': snapshot_module.app.info.name,
        'fs_type': storage.get_filesystem_type(),
        'fs_types_supported': snapshot_module.fs_types_supported,
    }
    return TemplateResponse(request, 'snapshot_not_supported.html',
                            template_data)


def index(request):
    """Show snapshot list."""
    if not snapshot_module.is_supported():
        return not_supported_view(request)

    status = get_configuration()
    if request.method == 'POST':
        form = SnapshotForm(request.POST)
        if 'update' in request.POST and form.is_valid():
            update_configuration(request, status, form.cleaned_data)
            status = get_configuration()
            form = SnapshotForm(initial=status)
    else:
        form = SnapshotForm(initial=status)

    return TemplateResponse(
        request, 'snapshot.html', {
            'app_info': snapshot_module.app.info,
            'title': snapshot_module.app.info.name,
            'subsubmenu': subsubmenu,
            'form': form
        })


def manage(request):
    """Show snapshot list."""
    if not snapshot_module.is_supported():
        return not_supported_view(request)

    if request.method == 'POST':
        if 'create' in request.POST:
            actions.superuser_run('snapshot', ['create'])
            messages.success(request, _('Created snapshot.'))
        if 'delete_selected' in request.POST:
            if request.POST.getlist('snapshot_list'):
                snapshot_to_delete = request.POST.getlist('snapshot_list')
                request.session['snapshots'] = snapshot_to_delete
                return redirect(reverse('snapshot:delete-selected'))

    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)
    has_deletable_snapshots = any(
        [snapshot for snapshot in snapshots[1:] if not snapshot['is_default']])

    return TemplateResponse(
        request, 'snapshot_manage.html', {
            'title': snapshot_module.app.info.name,
            'app_info': snapshot_module.app.info,
            'snapshots': snapshots,
            'has_deletable_snapshots': has_deletable_snapshots,
            'subsubmenu': subsubmenu,
        })


def update_configuration(request, old_status, new_status):
    """Update configuration of snapshots."""
    def make_config(args):
        key, stamp = args[0], args[1]
        if old_status[key] != new_status[key]:
            if 'limit' in key:
                return stamp.format('0-{}'.format(new_status[key]))

            return stamp.format(new_status[key])

        return None

    config = filter(
        None,
        map(make_config, [
            ('enable_timeline_snapshots', 'TIMELINE_CREATE={}'),
            ('hourly_limit', 'TIMELINE_LIMIT_HOURLY={}'),
            ('daily_limit', 'TIMELINE_LIMIT_DAILY={}'),
            ('weekly_limit', 'TIMELINE_LIMIT_WEEKLY={}'),
            ('monthly_limit', 'TIMELINE_LIMIT_MONTHLY={}'),
            ('yearly_limit', 'TIMELINE_LIMIT_YEARLY={}'),
            ('free_space', 'FREE_LIMIT={}'),
        ]))

    if old_status['enable_software_snapshots'] != new_status[
            'enable_software_snapshots']:
        if new_status['enable_software_snapshots'] == 'yes':
            actions.superuser_run('snapshot', ['disable-apt-snapshot', 'no'])
        else:
            actions.superuser_run('snapshot', ['disable-apt-snapshot', 'yes'])

    try:
        actions.superuser_run('snapshot', ['set-config', " ".join(config)])

        messages.success(request, _('Storage snapshots configuration updated'))
    except ActionError as exception:
        messages.error(
            request,
            _('Action error: {0} [{1}] [{2}]').format(exception.args[0],
                                                      exception.args[1],
                                                      exception.args[2]))


def delete_selected(request):
    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    if request.method == 'POST':
        if 'snapshots' in request.session:
            to_delete = request.session['snapshots']
            try:
                if to_delete == len(snapshots):
                    actions.superuser_run('snapshot', ['delete_all'])
                    messages.success(request, _('Deleted all snapshots'))
                else:
                    for snapshot in to_delete:
                        actions.superuser_run('snapshot', ['delete', snapshot])
                    messages.success(request, _('Deleted selected snapshots'))
            except ActionError as exception:
                if 'Config is in use.' in exception.args[2]:
                    messages.error(
                        request,
                        _('Snapshot is currently in use. '
                          'Please try again later.'))
                else:
                    raise

            return redirect(reverse('snapshot:manage'))

    if 'snapshots' in request.session:
        data = request.session['snapshots']
        to_delete = list(filter(lambda x: x['number'] in data, snapshots))

        return TemplateResponse(request, 'snapshot_delete_selected.html', {
            'title': _('Delete Snapshots'),
            'snapshots': to_delete
        })


def rollback(request, number):
    """Show confirmation to rollback to a snapshot."""
    if request.method == 'POST':
        actions.superuser_run('snapshot', ['rollback', number])
        messages.success(
            request,
            _('Rolled back to snapshot #{number}.').format(number=number))
        messages.warning(
            request,
            _('The system must be restarted to complete the rollback.'))
        return redirect(reverse('power:restart'))

    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    snapshot = None
    for current_snapshot in snapshots:
        if current_snapshot['number'] == number:
            snapshot = current_snapshot

    return TemplateResponse(request, 'snapshot_rollback.html', {
        'title': _('Rollback to Snapshot'),
        'snapshot': snapshot
    })
