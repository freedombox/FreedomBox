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

from . import get_configuration
from .forms import SnapshotForm

subsubmenu = [{
    'url': reverse_lazy('snapshot:index'),
    'text': ugettext_lazy('Configure')
}, {
    'url': reverse_lazy('snapshot:manage'),
    'text': ugettext_lazy('Manage Snapshots')
}]


def index(request):
    """Show snapshot list."""
    status = get_configuration()
    if request.method == 'POST':
        form = SnapshotForm(request.POST)
        if 'update' in request.POST and form.is_valid():
            update_configuration(request, status, form.cleaned_data)
            status = get_configuration()
            form = SnapshotForm(initial=status)
    else:
        form = SnapshotForm(initial=status)

    return TemplateResponse(request, 'snapshot.html', {
        'title': snapshot_module.name,
        'description': snapshot_module.description,
        'manual_page': snapshot_module.manual_page,
        'subsubmenu': subsubmenu,
        'form': form
    })


def manage(request):
    """Show snapshot list."""
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

    return TemplateResponse(request, 'snapshot_manage.html', {
        'snapshots': snapshots,
        'has_deletable_snapshots': has_deletable_snapshots,
        'subsubmenu': subsubmenu,
    })


def update_configuration(request, old_status, new_status):
    """Update configuration of snapshots."""

    def make_config(args):
        key, stamp = args[0], args[1]
        if old_status[key] != new_status[key]:
            return stamp.format(new_status[key])
        else:
            return None

    new_status['number_min_age'] = int(new_status['number_min_age']) * 86400

    config = filter(None,
                    map(make_config, [
                        ('enable_timeline_snapshots', 'TIMELINE_CREATE={}'),
                        ('hourly_limit', 'TIMELINE_LIMIT_HOURLY={}'),
                        ('daily_limit', 'TIMELINE_LIMIT_DAILY={}'),
                        ('weekly_limit', 'TIMELINE_LIMIT_WEEKLY={}'),
                        ('monthly_limit', 'TIMELINE_LIMIT_MONTHLY={}'),
                        ('yearly_limit', 'TIMELINE_LIMIT_YEARLY={}'),
                        ('number_min_age', 'NUMBER_MIN_AGE={}'),
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
        messages.error(request,
                       _('Action error: {0} [{1}] [{2}]').format(
                           exception.args[0], exception.args[1],
                           exception.args[2]))


def delete_selected(request):
    output = actions.superuser_run('snapshot', ['list'])
    snapshots = json.loads(output)

    if request.method == 'POST':
        if 'snapshots' in request.session:
            to_delete = request.session['snapshots']
            if to_delete == len(snapshots):
                actions.superuser_run('snapshot', ['delete_all'])
                messages.success(request, _('Deleted all snapshots'))
            else:
                for snapshot in to_delete:
                    actions.superuser_run('snapshot', ['delete', snapshot])
                messages.success(request, _('Deleted selected snapshots'))
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
