# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Ejabberd module
"""

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions
from plinth.modules import ejabberd
from plinth.views import AppView

from .forms import EjabberdForm


class EjabberdAppView(AppView):
    """Show ejabberd as a service."""
    app_id = 'ejabberd'
    template_name = 'ejabberd.html'
    form_class = EjabberdForm
    port_forwarding_info = ejabberd.port_forwarding_info

    def get_initial(self):
        initdict = super().get_initial()
        initdict.update({'MAM_enabled': self.is_MAM_enabled()})
        return initdict

    def get_context_data(self, *args, **kwargs):
        """Add service to the context data."""
        context = super().get_context_data(*args, **kwargs)
        domains = ejabberd.get_domains()
        context['domainname'] = domains[0] if domains else None
        return context

    def form_valid(self, form):
        """Enable/disable a service and set messages."""
        old_status = form.initial
        new_status = form.cleaned_data
        app_same = old_status['is_enabled'] == new_status['is_enabled']
        mam_same = old_status['MAM_enabled'] == new_status['MAM_enabled']

        if app_same and mam_same:
            # TODO: find a more reliable/official way to check whether the
            # request has messages attached.
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_status['is_enabled']:
                self.app.enable()
            else:
                self.app.disable()

        if not mam_same:
            # note ejabberd action "enable" or "disable" restarts, if running
            if new_status['MAM_enabled']:
                actions.superuser_run('ejabberd', ['mam', 'enable'])
                messages.success(self.request,
                                 _('Message Archive Management enabled'))
            else:
                actions.superuser_run('ejabberd', ['mam', 'disable'])
                messages.success(self.request,
                                 _('Message Archive Management disabled'))

        return super().form_valid(form)

    def is_MAM_enabled(self):
        """Return whether Message Archive Management (MAM) is enabled."""
        output = actions.superuser_run('ejabberd', ['mam', 'status'])
        return output.strip() == 'enabled'
