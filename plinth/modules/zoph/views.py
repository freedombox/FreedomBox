# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Zoph photo organiser."""

import logging

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import TemplateView

from plinth import app as app_module
from plinth import views

from . import privileged
from .forms import ZophForm

logger = logging.getLogger(__name__)


class SetupView(TemplateView):
    """Show zoph setup page."""

    template_name = 'zoph-pre-setup.html'
    success_url = reverse_lazy('zoph:index')

    def get_context_data(self, *args, **kwargs):
        """Provide context data to the template."""
        context = super().get_context_data(**kwargs)
        app = app_module.App.get('zoph')
        context['title'] = app.info.name
        context['app_info'] = app.info
        return context

    def post(self, _request, *args, **kwargs):
        """Handle form submission."""
        admin_user = self.request.user.get_username()
        privileged.set_configuration(admin_user=admin_user)
        return HttpResponseRedirect(reverse_lazy('zoph:index'))


class ZophAppView(views.AppView):
    """App configuration page."""

    form_class = ZophForm
    app_id = 'zoph'

    def dispatch(self, request, *args, **kwargs):
        """Redirect to setup page if setup is not done yet."""
        if not privileged.is_configured():
            return redirect('zoph:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_initial(self):
        """Get the current settings from Zoph."""
        status = super().get_initial()
        config = privileged.get_configuration()
        status['enable_osm'] = (config['maps.provider'] == 'osm')
        return status

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_status = form.initial
        new_status = form.cleaned_data
        if old_status['enable_osm'] != new_status['enable_osm']:
            try:
                privileged.set_configuration(
                    enable_osm=new_status['enable_osm'])
                messages.success(self.request, _('Configuration updated.'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)
