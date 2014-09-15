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
    next = request.GET.get('next', reverse('vault:services'))
    services[module]['enable']()
    if not services[module]['synchronous']:
        msg = """Enabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)


def disable_service(request, module):
    next = request.GET.get('next', reverse('vault:services'))
    services[module]['disable']()
    if not services[module]['synchronous']:
        msg = """Disabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)
