# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the SSH module
"""
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth.modules import ssh
from plinth.views import AppView

from . import is_password_authentication_disabled
from .forms import SSHServerForm


class SshAppView(AppView):
    app_id = 'ssh'
    template_name = 'ssh.html'
    form_class = SSHServerForm

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['host_keys'] = ssh.get_host_keys()

        return context

    def get_initial(self):
        """Initial form value"""
        initial = super().get_initial()
        initial.update({
            'password_auth_disabled': is_password_authentication_disabled(),
        })

        return initial

    def form_valid(self, form):
        """Apply changes from the form"""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        def is_field_changed(field):
            return old_config[field] != new_config[field]

        passwd_auth_changed = is_field_changed('password_auth_disabled')
        if passwd_auth_changed:
            if new_config['password_auth_disabled']:
                passwd_auth = 'no'
                message = _('SSH authentication with password disabled.')
            else:
                passwd_auth = 'yes'
                message = _('SSH authentication with password enabled.')

            actions.superuser_run(
                'ssh', ['set-password-config', '--value', passwd_auth])
            actions.superuser_run('service', ['reload', 'ssh'])
            messages.success(self.request, message)

        return super().form_valid(form)
