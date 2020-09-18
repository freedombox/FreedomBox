# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the Tahoe-LAFS module
"""
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import FormView

from plinth.forms import DomainSelectionForm
from plinth.modules import names, tahoe
from plinth.views import AppView


class TahoeSetupView(FormView):
    """Show tahoe-lafs setup page."""
    template_name = 'tahoe-pre-setup.html'
    form_class = DomainSelectionForm
    success_url = reverse_lazy('tahoe:index')

    def form_valid(self, form):
        domain_name = form.cleaned_data['domain_name']
        tahoe.post_setup(domain_name)
        return super().form_valid(form)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = tahoe.app.info.description
        context['title'] = tahoe.app.info.name
        context['domain_names'] = names.components.DomainName.list_names(
            'tahoe-plinth')

        return context


class TahoeAppView(AppView):
    """Show tahoe-lafs service page."""
    app_id = 'tahoe'
    template_name = 'tahoe-post-setup.html'

    def dispatch(self, request, *args, **kwargs):
        if not tahoe.is_setup():
            return redirect('tahoe:setup')

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(**kwargs)
        context['domain_name'] = tahoe.get_configured_domain_name()
        context['introducers'] = tahoe.get_introducers()
        context['local_introducer'] = tahoe.get_local_introducer()

        return context


def add_introducer(request):
    if request.method == 'POST':
        tahoe.add_introducer((request.POST['pet_name'], request.POST['furl']))
        return redirect('tahoe:index')


def remove_introducer(request, introducer):
    if request.method == 'POST':
        tahoe.remove_introducer(introducer)
        return redirect('tahoe:index')
