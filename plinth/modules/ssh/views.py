# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the SSH app."""

from django.contrib import messages
from django.utils.translation import gettext_lazy as _

from plinth.modules import ssh
from plinth.privileged import service as service_privileged
from plinth.views import AppView

from . import privileged
from .forms import SSHServerForm


class SshAppView(AppView):
    """Show ssh app main page."""

    app_id = 'ssh'
    template_name = 'ssh.html'
    form_class = SSHServerForm

    def get_context_data(self, *args, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['host_keys'] = ssh.get_host_keys()

        return context

    def get_initial(self):
        """Return initial values of the form."""
        initial = super().get_initial()
        initial.update({
            'password_auth_disabled':
                not privileged.is_password_authentication_enabled(),
        })

        return initial

    def form_valid(self, form):
        """Apply changes from the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        def is_field_changed(field):
            return old_config[field] != new_config[field]

        passwd_auth_changed = is_field_changed('password_auth_disabled')
        if passwd_auth_changed:
            privileged.set_password_authentication(
                not new_config['password_auth_disabled'])
            service_privileged.reload('ssh')
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)
