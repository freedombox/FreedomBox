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
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
import json

from plinth import actions
from plinth.modules import snapshot as snapshot_module


def index(request):
    """Show snapshot list."""
    if request.method == 'POST':
        actions.superuser_run('snapshot', ['create'])
        messages.success(request, _('Created snapshot.'))

    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    return TemplateResponse(request, 'snapshot.html',
                            {'title': snapshot_module.title,
                             'description': snapshot_module.description,
                             'snapshots': snapshots})


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
