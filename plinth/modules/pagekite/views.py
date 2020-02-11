#
# This file is part of FreedomBox.
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

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, View
from django.views.generic.edit import FormView

from plinth.modules import pagekite

from . import utils
from .forms import (AddCustomServiceForm, ConfigurationForm,
                    DeleteCustomServiceForm)


class ContextMixin(object):
    """Mixin to add 'subsubmenu' and 'title' to the context.

    Also adds the requirement of all necessary packages to be installed
    """
    def get_context_data(self, **kwargs):
        """Use self.title and the module-level subsubmenu"""
        context = super(ContextMixin, self).get_context_data(**kwargs)
        context['app_info'] = pagekite.app.info
        context['title'] = pagekite.app.info.name
        context['is_enabled'] = pagekite.app.is_enabled()
        return context

    def dispatch(self, *args, **kwargs):
        return super(ContextMixin, self).dispatch(*args, **kwargs)


class DeleteServiceView(ContextMixin, View):
    def post(self, request):
        form = DeleteCustomServiceForm(request.POST)
        if form.is_valid():
            form.delete(request)
        return HttpResponseRedirect(reverse('pagekite:index'))


class AddCustomServiceView(ContextMixin, TemplateView):
    template_name = 'pagekite_custom_services.html'

    def get_context_data(self, *args, **kwargs):
        context = super(AddCustomServiceView,
                        self).get_context_data(*args, **kwargs)
        unused, custom_services = utils.get_pagekite_services()
        for service in custom_services:
            service['form'] = AddCustomServiceForm(initial=service)
        context['custom_services'] = [
            utils.prepare_service_for_display(service)
            for service in custom_services
        ]
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
        return HttpResponseRedirect(reverse('pagekite:index'))


class ConfigurationView(ContextMixin, FormView):
    template_name = 'pagekite_configure.html'
    form_class = ConfigurationForm
    prefix = 'pagekite'
    success_url = reverse_lazy('pagekite:index')

    def get_context_data(self, *args, **kwargs):
        context = super(ConfigurationView,
                        self).get_context_data(*args, **kwargs)
        unused, custom_services = utils.get_pagekite_services()
        for service in custom_services:
            service['form'] = AddCustomServiceForm(initial=service)
        context['custom_services'] = [
            utils.prepare_service_for_display(service)
            for service in custom_services
        ]
        context.update(utils.get_kite_details())
        return context

    def get_initial(self):
        return utils.get_pagekite_config()

    def form_valid(self, form):
        form.save(self.request)
        return super(ConfigurationView, self).form_valid(form)
