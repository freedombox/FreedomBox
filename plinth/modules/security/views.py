# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for security module
"""

from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _

from plinth import action_utils, actions
from plinth.modules import security

from .forms import SecurityForm


def index(request):
    """Serve the security configuration form"""
    status = get_status(request)

    form = None

    if request.method == 'POST':
        form = SecurityForm(request.POST, initial=status, prefix='security')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status(request)
            form = SecurityForm(initial=status, prefix='security')
    else:
        form = SecurityForm(initial=status, prefix='security')

    return TemplateResponse(request, 'security.html', {
        'app_info': security.app.info,
        'form': form,
    })


def get_status(request):
    """Return the current status"""
    return {
        'restricted_access': security.get_restricted_access_enabled(),
        'fail2ban_enabled': action_utils.service_is_enabled('fail2ban')
    }


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    if old_status['restricted_access'] != new_status['restricted_access']:
        try:
            security.set_restricted_access(new_status['restricted_access'])
        except Exception as exception:
            messages.error(
                request,
                _('Error setting restricted access: {exception}').format(
                    exception=exception))
        else:
            messages.success(request, _('Updated security configuration'))

    if old_status['fail2ban_enabled'] != new_status['fail2ban_enabled']:
        if new_status['fail2ban_enabled']:
            actions.superuser_run('service', ['enable', 'fail2ban'])
        else:
            actions.superuser_run('service', ['disable', 'fail2ban'])


def report(request):
    """Serve the security report page"""
    apps_report = security.get_apps_report()
    return TemplateResponse(
        request, 'security_report.html', {
            'title':
                _('Security Report'),
            'freedombox_report':
                apps_report.pop('freedombox'),
            'apps_report':
                sorted(apps_report.values(), key=lambda app: app['name']),
        })
