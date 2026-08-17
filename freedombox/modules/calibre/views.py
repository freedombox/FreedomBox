# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the calibre module."""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.edit import FormView

from plinth import app as app_module
from plinth import views

from . import forms, privileged


class CalibreAppView(views.AppView):
    """Serve configuration form."""

    app_id = 'calibre'
    template_name = 'calibre.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['libraries'] = privileged.list_libraries()
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
            privileged.create_library(form.cleaned_data['name'])
        except Exception as error:
            self.success_message = ''
            messages.error(
                self.request, "{0} {1}".format(
                    _('An error occurred while creating the library.'),
                    str(error)))

        return super().form_valid(form)


def delete_library(request, name):
    """View to delete a library."""
    if name not in privileged.list_libraries():
        raise Http404

    if request.method == 'POST':
        try:
            privileged.delete_library(name)
            messages.success(request, _('{name} deleted.').format(name=name))
        except Exception as error:
            messages.error(
                request,
                _('Could not delete {name}: {error}').format(
                    name=name, error=error))
        return redirect(reverse_lazy('calibre:index'))

    return TemplateResponse(request, 'calibre-delete-library.html', {
        'title': app_module.App.get('calibre').info.name,
        'name': name
    })
