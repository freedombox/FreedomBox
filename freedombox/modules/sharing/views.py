# SPDX-License-Identifier: AGPL-3.0-or-later
"""Views for the sharing app."""

from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import FormView

from plinth.views import AppView

from . import privileged
from .forms import AddShareForm


class SharingAppView(AppView):
    """Sharing configuration page."""

    app_id = 'sharing'
    template_name = 'sharing.html'

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['shares'] = privileged.list_shares()
        return context


class AddShareView(SuccessMessageMixin, FormView):
    """View to add a new share."""

    form_class = AddShareForm
    prefix = 'sharing'
    template_name = 'sharing_add_edit.html'
    success_url = reverse_lazy('sharing:index')
    success_message = _('Share added.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add Share')
        return context

    def form_valid(self, form):
        """Add the share on valid form submission."""
        _add_share(form.cleaned_data)
        return super().form_valid(form)


class EditShareView(SuccessMessageMixin, FormView):
    """View to edit an existing share."""

    form_class = AddShareForm
    prefix = 'sharing'
    template_name = 'sharing_add_edit.html'
    success_url = reverse_lazy('sharing:index')
    success_message = _('Share edited.')

    def get_context_data(self, **kwargs):
        """Return additional context for rendering the template."""
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Share')
        return context

    def get_initial(self):
        """Load information about share being edited."""
        try:
            return [
                share for share in privileged.list_shares()
                if share['name'] == self.kwargs['name']
            ][0]
        except IndexError:
            raise Http404

    def form_valid(self, form):
        """Add the share on valid form submission."""
        if form.initial != form.cleaned_data:
            privileged.remove(form.initial['name'])
            _add_share(form.cleaned_data)

        return super().form_valid(form)


def _add_share(form_data):
    privileged.add(form_data['name'], form_data['path'], form_data['groups'],
                   form_data['is_public'])


@require_POST
def remove(request, name):
    """View to remove a share."""
    privileged.remove(name)
    messages.success(request, _('Share deleted.'))
    return redirect(reverse_lazy('sharing:index'))
