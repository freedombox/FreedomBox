# SPDX-License-Identifier: AGPL-3.0-or-later

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import View
from django.views.generic.edit import FormView

from plinth.views import AppView

from . import privileged
from .forms import (AddCustomServiceForm, ConfigurationForm,
                    DeleteCustomServiceForm)


class DeleteServiceView(View):

    def post(self, request):
        form = DeleteCustomServiceForm(request.POST)
        if form.is_valid():
            form.delete(request)
        return HttpResponseRedirect(reverse('pagekite:index'))


class AddCustomServiceView(FormView):
    """View to add a new custom PageKite service."""
    form_class = AddCustomServiceForm
    template_name = 'pagekite_custom_services.html'
    success_url = reverse_lazy('pagekite:index')

    def get_context_data(self, *args, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(*args, **kwargs)
        context['title'] = _('Add custom PageKite service')
        return context

    def form_valid(self, form):
        """Add a custom service."""
        form.save(self.request)
        return super().form_valid(form)


class ConfigurationView(AppView):
    app_id = 'pagekite'
    template_name = 'pagekite_configure.html'
    form_class = ConfigurationForm
    prefix = 'pagekite'
    success_url = reverse_lazy('pagekite:index')

    def __init__(self, *args, **kwargs):
        """Load and store the current configuration."""
        super().__init__(*args, **kwargs)
        self.config = privileged.get_config()
        self.initial = self.config

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        for service in self.config['custom_services']:
            service['delete_form'] = DeleteCustomServiceForm(initial=service)
        context.update(self.config)
        return context

    def form_valid(self, form):
        form.save(self.request)
        return super().form_valid(form)
