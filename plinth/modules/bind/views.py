# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for BIND module.
"""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth.modules import bind, names
from plinth.views import AppView

from . import get_config
from .forms import BindForm


class BindAppView(AppView):  # pylint: disable=too-many-ancestors
    """A specialized view for configuring Bind."""
    app_id = 'bind'
    form_class = BindForm
    template_name = 'bind.html'

    def get_context_data(self, *args, **kwargs):
        """
        Get/append information for domains bind is configured to respond for
        and additional names from the names module
        """
        context = super().get_context_data(**kwargs)

        served_domains = bind.get_served_domains()
        context['domains_table'] = []
        for key, val in served_domains.items():
            if key == 'localhost.':
                continue

            context['domains_table'].append({
                'type': 'Domain Name',
                'domain_name': key[:-1:],
                'serving': 'Yes',
                'ip_address': ', '.join(val),
            })

        for item in names.components.DomainName.list():
            context['domains_table'].append({
                'type': item.domain_type.display_name,
                'domain_name': item.name,
                'serving': '-',
                'ip_address': ''
            })

        return context

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update(get_config())
        return initial

    def form_valid(self, form):
        """Change the configurations of Bind service."""
        data = form.cleaned_data
        old_config = get_config()

        if old_config['forwarders'] != data['forwarders'] \
           or old_config['enable_dnssec'] != data['enable_dnssec']:
            dnssec_setting = 'enable' if data['enable_dnssec'] else 'disable'
            actions.superuser_run('bind', [
                'configure', '--forwarders', data['forwarders'], '--dnssec',
                dnssec_setting
            ])
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
