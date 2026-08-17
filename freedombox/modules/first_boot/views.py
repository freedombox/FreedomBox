# SPDX-License-Identifier: AGPL-3.0-or-later

from django import http
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from plinth.modules import first_boot

from .forms import FirstbootWizardSecretForm


class WelcomeView(FormView):
    """Show the welcome screen."""
    form_class = FirstbootWizardSecretForm
    template_name = 'firstboot_welcome.html'

    def form_valid(self, form):
        """If form is valid, mark this step as done and move to next step."""
        self.request.session['firstboot_secret_provided'] = True
        first_boot.mark_step_done('firstboot_welcome')
        return http.HttpResponseRedirect(reverse(first_boot.next_step()))

    def get_context_data(self, **kwargs):
        """Add network connections to context list."""
        context = super().get_context_data(**kwargs)
        show_prompt = first_boot.firstboot_wizard_secret_exists()
        context['show_wizard_password_prompt'] = show_prompt
        return context


class CompleteView(TemplateView):
    """Show next steps after all firstboot wizard steps are done."""

    template_name = 'firstboot_complete.html'

    def get_context_data(self, **kwargs):
        """Add network connections to context list."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Setup Complete')
        return context
