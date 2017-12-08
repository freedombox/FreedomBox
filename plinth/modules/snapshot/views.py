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
Views for snapshot module.
"""

from django.contrib import messages
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import ugettext as _
import json

from plinth.errors import ActionError
from .forms import SnapshotForm
from plinth import actions
from plinth.modules import snapshot as snapshot_module
from . import is_timeline_snapshots_enabled


def index(request):
    """Show snapshot list."""
    status = get_status()
    if request.method == 'POST':
        form = SnapshotForm(request.POST, prefix='snapshot')
        if 'create' in request.POST:
            actions.superuser_run('snapshot', ['create'])
            messages.success(request, _('Created snapshot.'))
        if 'update' in request.POST and form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = SnapshotForm(initial=status, prefix='snapshot')
    else:
        form = SnapshotForm(initial=status, prefix='snapshot')

    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    return TemplateResponse(request, 'snapshot.html',
                            {'title': snapshot_module.name,
                             'description': snapshot_module.description,
                             'snapshots': snapshots,
                             'form': form})


def delete(request, number):
    """Show confirmation to delete a snapshot."""
    if request.method == 'POST':
        actions.superuser_run('snapshot', ['delete', number])
        messages.success(
            request, _('Deleted snapshot #{number}.').format(number=number))
        return redirect(reverse('snapshot:index'))

    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    snapshot = None
    for current_snapshot in snapshots:
        if current_snapshot['number'] == number:
            snapshot = current_snapshot

    return TemplateResponse(request, 'snapshot_delete.html',
                            {'title': _('Delete Snapshot'),
                             'snapshot': snapshot})


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

    return TemplateResponse(request, 'snapshot_rollback.html',
                            {'title': _('Rollback to Snapshot'),
                             'snapshot': snapshot})


def get_status():
    return {'enable_timeline_snapshots': is_timeline_snapshots_enabled()}


def _apply_changes(request, old_status, new_status):
    """Try to apply changes and handle errors."""
    try:
        __apply_changes(request, old_status, new_status)
    except ActionError as exception:
        messages.error(request, _('Action error: {0} [{1}] [{2}]').format(
          exception.args[0], exception.args[1], exception.args[2]))


def __apply_changes(request, old_status, new_status):
    if old_status['enable_timeline_snapshots'] != new_status['enable_timeline_snapshots']:
        timeline_create = "TIMELINE_CREATE=yes" if new_status['enable_timeline_snapshots'] else "TIMELINE_CREATE=no"
        actions.superuser_run('snapshot', ['configure', timeline_create])
        messages.success(request, _('Timeline Snapshots configuration updated'))
