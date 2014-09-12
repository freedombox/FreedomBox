import importlib

from django.views.generic import TemplateView
from django.core.urlresolvers import reverse
from django.contrib import messages

from .registry import APPS, SERVICES, STATUSLINE_ITEMS

class Apps(TemplateView):
    template_name = 'vault_apps.html'

    def get_context_data(self, **kwargs):
        context = super(Apps, self).get_context_data(**kwargs)
        context['apps'] = APPS
        return context

class Services(TemplateView):
    template_name = 'vault_services.html'

    def get_context_data(self, **kwargs):
        context = super(Services, self).get_context_data(**kwargs)
        context['services'] = SERVICES
        return context
