from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView

from .registry import apps, services, statusline_items


class Apps(TemplateView):
    template_name = 'vault_apps.html'

    def get_context_data(self, **kwargs):
        context = super(Apps, self).get_context_data(**kwargs)
        context['apps'] = apps
        context['statusline_items'] = statusline_items
        return context


class Services(TemplateView):
    template_name = 'vault_services.html'

    def get_context_data(self, **kwargs):
        context = super(Services, self).get_context_data(**kwargs)
        context['services'] = services
        context['statusline_items'] = statusline_items
        return context


def enable_service(request, module):
    try:
        services[module]['enable']()
    except KeyError:
        messages.error(request, "Could not enable service %s" % module)
    return HttpResponseRedirect(reverse('vault:services'))


def disable_service(request, module):
    services[module]['disable']()
    return HttpResponseRedirect(reverse('vault:services'))
