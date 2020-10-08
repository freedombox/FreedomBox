# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the calibre module.
"""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic.edit import FormView

from plinth import actions, views
from plinth.modules import calibre

from . import forms


class CalibreAppView(views.AppView):
    """Serve configuration form."""
    app_id = 'calibre'
    template_name = 'calibre.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['libraries'] = calibre.list_libraries()
        return context


class CreateLibraryView(SuccessMessageMixin, FormView):
    """View to create an empty library."""
    form_class = forms.CreateLibraryForm
    prefix = 'calibre'
    template_name = 'form.html'
    success_url = reverse_lazy('calibre:index')
    success_message = _('Library created.')

    def form_valid(self, form):
        """Create the library on valid form submission."""
        try:
            calibre.create_library(form.cleaned_data['name'])
        except actions.ActionError as error:
            self.success_message = ''
            error_text = error.args[2].split('\n')[0]
            messages.error(
                self.request, "{0} {1}".format(
                    _('An error occurred while creating the library.'),
                    error_text))

        return super().form_valid(form)


def delete_library(request, name):
    """View to delete a library."""
    if name not in calibre.list_libraries():
        raise Http404

    if request.method == 'POST':
        try:
            calibre.delete_library(name)
            messages.success(request, _('{name} deleted.').format(name=name))
        except actions.ActionError as error:
            messages.error(
                request,
                _('Could not delete {name}: {error}').format(
                    name=name, error=error))
        return redirect(reverse_lazy('calibre:index'))

    return TemplateResponse(request, 'calibre-delete-library.html', {
        'title': calibre.app.info.name,
        'name': name
    })
