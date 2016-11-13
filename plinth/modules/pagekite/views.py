#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import reverse, reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, TemplateView
from django.views.generic.edit import FormView

from . import utils
from .forms import ConfigurationForm, StandardServiceForm, \
    AddCustomServiceForm, DeleteCustomServiceForm, FirstBootForm
from plinth import cfg
from plinth.errors import DomainRegistrationError
from plinth.modules import first_boot
from plinth.modules import pagekite

subsubmenu = [{'url': reverse_lazy('pagekite:index'),
               'text': _('About PageKite')},
              {'url': reverse_lazy('pagekite:configure'),
               'text': _('Configure PageKite')},
              {'url': reverse_lazy('pagekite:standard-services'),
               'text': _('Standard Services')},
              {'url': reverse_lazy('pagekite:custom-services'),
               'text': _('Custom Services')}]


def index(request):
    """Serve introduction page"""
    return TemplateResponse(request, 'pagekite_introduction.html',
                            {'title': pagekite.title,
                             'description': pagekite.description,
                             'subsubmenu': subsubmenu})


class ContextMixin(object):
    """Mixin to add 'subsubmenu' and 'title' to the context.

    Also adds the requirement of all necessary packages to be installed
    """

    def get_context_data(self, **kwargs):
        """Use self.title and the module-level subsubmenu"""
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['title'] = getattr(self, 'title', '')
        context['subsubmenu'] = subsubmenu
        return context

    def dispatch(self, *args, **kwargs):
        return super(ContextMixin, self).dispatch(*args, **kwargs)


class DeleteServiceView(ContextMixin, View):
    def post(self, request):
        form = DeleteCustomServiceForm(request.POST)
        if form.is_valid():
            form.delete(request)
        return HttpResponseRedirect(reverse('pagekite:custom-services'))


class CustomServiceView(ContextMixin, TemplateView):
    template_name = 'pagekite_custom_services.html'

    def get_context_data(self, *args, **kwargs):
        context = super(CustomServiceView, self).get_context_data(*args,
                                                                  **kwargs)
        unused, custom_services = utils.get_pagekite_services()
        for service in custom_services:
            service['form'] = AddCustomServiceForm(initial=service)
        context['custom_services'] = [
            utils.prepare_service_for_display(service)
            for service in custom_services]
        context.update(utils.get_kite_details())
        return context

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = AddCustomServiceForm(prefix="custom")
        context['form'] = form
        return self.render_to_response(context)

    def post(self, request):
        form = AddCustomServiceForm(request.POST, prefix="custom")
        if form.is_valid():
            form.save(request)
            form = AddCustomServiceForm(prefix="custom")

        context = self.get_context_data()
        context['form'] = form

        return self.render_to_response(context)


class StandardServiceView(ContextMixin, FormView):
    template_name = 'pagekite_standard_services.html'
    title = 'PageKite Standard Services'
    form_class = StandardServiceForm
    success_url = reverse_lazy('pagekite:standard-services')

    def get_initial(self):
        return utils.get_pagekite_services()[0]

    def form_valid(self, form):
        form.save(self.request)
        return super(StandardServiceView, self).form_valid(form)


class ConfigurationView(ContextMixin, FormView):
    template_name = 'pagekite_configure.html'
    form_class = ConfigurationForm
    prefix = 'pagekite'
    success_url = reverse_lazy('pagekite:configure')

    def get_initial(self):
        return utils.get_pagekite_config()

    def form_valid(self, form):
        form.save(self.request)
        return super(ConfigurationView, self).form_valid(form)


class FirstBootView(FormView):
    """First boot (optional) setup of the Pagekite subdomain."""
    template_name = 'pagekite_firstboot.html'
    form_class = FirstBootForm

    def get(self, request, *args, **kwargs):
        """Skip if this first boot step if it is not relavent."""
        if not cfg.danube_edition:
            first_boot.mark_step_done('pagekite_firstboot')
            return HttpResponseRedirect(reverse(first_boot.next_step()))

        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        """Act on valid form submission."""
        try:
            form.register_domain()
        except DomainRegistrationError as error:
            messages.error(self.request, error)
            return self.form_invalid(form)

        form.setup_pagekite()
        first_boot.mark_step_done('pagekite_firstboot')
        message = _('Pagekite setup finished. The HTTP and HTTPS services '
                    'are activated now.')
        messages.success(self.request, message)
        return HttpResponseRedirect(reverse(first_boot.next_step()))


def first_boot_skip(request):
    """Skip the first boot step."""
    first_boot.mark_step_done('pagekite_firstboot')
    return HttpResponseRedirect(reverse(first_boot.next_step()))
