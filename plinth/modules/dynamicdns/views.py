# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the dynamicsdns module.
"""

import datetime

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import views
from plinth.modules import dynamicdns

from .forms import ConfigureForm


class DynamicDNSAppView(views.AppView):
    """Serve configuration page."""
    app_id = 'dynamicdns'
    template_name = 'dynamicdns.html'
    form_class = ConfigureForm

    _error_messages = {
        'timeout': _('Connection timed out'),
        'gaierror': _('Could not find server'),
        'TimeoutError': _('Connection timed out'),
        'ConnectionRefusedError': _('Server refused connection'),
        'ValueError': _('Already up-to-date')
    }

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        status = dynamicdns.get_status()
        config = dynamicdns.get_config()
        domains_status = {}
        for domain_name, domain in status['domains'].items():
            if domain_name not in config['domains']:
                continue

            # Create naive datetime object in local timezone
            domain['timestamp'] = datetime.datetime.fromtimestamp(
                domain['timestamp'])
            domains_status[domain_name] = domain
            if domain['error_code'] in self._error_messages:
                domain['error_message'] = self._error_messages[
                    domain['error_code']]

        context['domains_status'] = domains_status
        return context

    def get_initial(self):
        """Get the current values for the form."""
        initial = super().get_initial()
        domains = dynamicdns.get_config()['domains']
        domain = list(domains.values())[0] if domains else {}
        initial.update(domain)
        return domain

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status != new_status:
            config = dynamicdns.get_config()
            try:
                del config['domains'][old_status['domain']]
            except KeyError:
                pass

            config['domains'][new_status['domain']] = new_status
            dynamicdns.set_config(config)
            if old_status.get('domain'):
                dynamicdns.notify_domain_removed(old_status['domain'])

            dynamicdns.notify_domain_added(new_status['domain'])
            messages.success(self.request, _('Configuration updated'))

        # Perform an immediate update, even when configuration is not changed.
        dynamicdns.update_dns(None)

        return super().form_valid(form)
