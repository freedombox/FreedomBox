# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for snapshot module."""

import urllib.parse

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from plinth import app as app_module
from plinth.modules import snapshot as snapshot_module
from plinth.modules import storage
from plinth.views import AppView

from . import get_configuration, privileged
from .forms import SnapshotForm

# i18n for snapshot descriptions
SNAPSHOT_DESCRIPTION_STRINGS = {
    'manually created': gettext_lazy('manually created'),
    'timeline': gettext_lazy('timeline'),
    'apt': gettext_lazy('apt'),
}

subsubmenu = [
    {
        'url': reverse_lazy('snapshot:index'),
        'text': gettext_lazy('Configure')
    },
    {
        'url': reverse_lazy('snapshot:manage'),
        'text': gettext_lazy('Manage Snapshots')
    },
]


def not_supported_view(request):
    """Show that snapshots are not supported on the system."""
    app = app_module.App.get('snapshot')
    template_data = {
        'app_info': app.info,
        'title': app.info.name,
        'fs_type': storage.get_filesystem_type(),
        'fs_types_supported': snapshot_module.fs_types_supported,
    }
    return TemplateResponse(request, 'snapshot_not_supported.html',
                            template_data)


class SnapshotAppView(AppView):
    """Show snapshot app main page."""

    app_id = 'snapshot'
    template_name = 'snapshot.html'
    form_class = SnapshotForm

    def dispatch(self, request, *args, **kwargs):
        """If snapshots are not supported, use a different view."""
        if not snapshot_module.is_supported():
            return not_supported_view(request)

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_configuration())
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        context = super().get_context_data(*args, **kwargs)
        context['subsubmenu'] = subsubmenu
        return context

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        if 'update' in self.request.POST:
            update_configuration(self.request, form.initial, form.cleaned_data)

        return super().form_valid(form)


def manage(request):
    """Show snapshot list."""
    if not snapshot_module.is_supported():
        return not_supported_view(request)

    if request.method == 'POST':
        if 'create' in request.POST:
            privileged.create()
            messages.success(request, _('Created snapshot.'))
        if 'delete_selected' in request.POST:
            to_delete = request.POST.getlist('snapshot_list')
            if to_delete:
                # Send values using GET params instead of session variables so
                # that snapshots can be deleted even when disk is full.
                params = [('snapshots', number) for number in to_delete]
                params = urllib.parse.urlencode(params)
                url = reverse('snapshot:delete-selected')
                return HttpResponseRedirect(f'{url}?{params}')

    snapshots = privileged.list_()
    has_deletable_snapshots = any([
        snapshot for snapshot in snapshots
        if not snapshot['is_default'] and not snapshot['is_active']
    ])

    app = app_module.App.get('snapshot')
    return TemplateResponse(
        request, 'snapshot_manage.html', {
            'title': app.info.name,
            'app_info': app.info,
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
            privileged.disable_apt_snapshot('no')
        else:
            privileged.disable_apt_snapshot('yes')

    try:
        privileged.set_config(list(config))
        messages.success(request, _('Storage snapshots configuration updated'))
    except Exception as exception:
        messages.error(
            request,
            _('Action error: {0} [{1}] [{2}]').format(exception.args[0],
                                                      exception.args[1],
                                                      exception.args[2]))


def delete_selected(request):
    """View to delete selected snapshots."""
    if request.method == 'POST':
        to_delete = set(request.POST.getlist('snapshots'))
    else:
        to_delete = set(request.GET.getlist('snapshots'))

    if not to_delete:
        return redirect(reverse('snapshot:manage'))

    snapshots = privileged.list_()
    snapshots_to_delete = [
        snapshot for snapshot in snapshots if snapshot['number'] in to_delete
        and not snapshot['is_active'] and not snapshot['is_default']
    ]

    if request.method == 'POST':
        try:
            for snapshot in snapshots_to_delete:
                privileged.delete(snapshot['number'])

            messages.success(request, _('Deleted selected snapshots'))
        except Exception as exception:
            if 'Config is in use.' in exception.args[2]:
                messages.error(
                    request,
                    _('Snapshot is currently in use. '
                      'Please try again later.'))
            else:
                raise

        return redirect(reverse('snapshot:manage'))

    return TemplateResponse(request, 'snapshot_delete_selected.html', {
        'title': _('Delete Snapshots'),
        'snapshots': snapshots_to_delete
    })


def rollback(request, number):
    """Show confirmation to rollback to a snapshot."""
    if request.method == 'POST':
        privileged.rollback(number)
        messages.success(
            request,
            _('Rolled back to snapshot #{number}.').format(number=number))
        messages.warning(
            request,
            _('The system must be restarted to complete the rollback.'))
        return redirect(reverse('power:restart'))

    snapshots = privileged.list_()
    snapshot = None
    for current_snapshot in snapshots:
        if current_snapshot['number'] == number:
            snapshot = current_snapshot

    return TemplateResponse(request, 'snapshot_rollback.html', {
        'title': _('Rollback to Snapshot'),
        'snapshot': snapshot
    })
