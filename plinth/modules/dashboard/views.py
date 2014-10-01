from django.core.urlresolvers import reverse
from django.contrib import messages
from django.http.response import HttpResponseRedirect
from django.views.generic import TemplateView

from .registry import apps, statusline_items


class Index(TemplateView):
    template_name = 'dashboard_index.html'

    def get_context_data(self, **kwargs):
        context = super(Index, self).get_context_data(**kwargs)
        context['apps'] = apps
        context['statusline_items'] = statusline_items
        return context


def enable_app(request, module):
    next = request.GET.get('next', reverse('dashboard:index'))
    apps[module]['enable']()
    if not apps[module]['synchronous']:
        msg = """Enabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)


def disable_app(request, module):
    next = request.GET.get('next', reverse('dashboard:index'))
    apps[module]['disable']()
    if not apps[module]['synchronous']:
        msg = """Disabling %s. It can take a couple of minutes until all
              changes take place.""" % module
        messages.success(request, msg)
    return HttpResponseRedirect(next)
