# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Views for the email app.
"""

from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from plinth.modules.email import dns
from plinth.views import AppView

from . import aliases as aliases_module
from . import forms, privileged


class EmailAppView(AppView):
    """Server configuration page."""
    app_id = 'email'
    form_class = forms.DomainForm
    template_name = 'email.html'

    def get_context_data(self, **kwargs):
        """Add additional context data for rendering the template."""
        context = super().get_context_data(**kwargs)
        context.update(privileged.domain.get_domains())
        return context

    def get_initial(self):
        """Return the initial values to populate in the form."""
        initial = super().get_initial()
        domains = privileged.domain.get_domains()
        initial['primary_domain'] = domains['primary_domain']
        return initial

    def form_valid(self, form):
        """Update the settings for changed domain values."""
        old_data = form.initial
        new_data = form.cleaned_data
        if old_data['primary_domain'] != new_data['primary_domain']:
            try:
                privileged.domain.set_all_domains(new_data['primary_domain'])
                messages.success(self.request, _('Configuration updated'))
            except Exception:
                messages.error(self.request,
                               _('An error occurred during configuration.'))

        return super().form_valid(form)


class DnsView(TemplateView):
    """Show the DNS records to configure on a given domain."""
    template_name = 'email-dns.html'

    def get_context_data(self, **kwargs):
        """Add additional context data for rendering the template."""
        domain = self.kwargs['domain']
        context = super().get_context_data(**kwargs)
        primary_domain = privileged.domain.get_domains()['primary_domain']
        context['primary_domain'] = primary_domain
        context['dns_entries'] = dns.get_entries(domain)
        context['reverse_dns_entries'] = dns.get_reverse_entries(domain)
        return context


class AliasView(FormView):
    """View to create, list, enable, disable and delete aliases.

    This view has two forms. Form to list (and manage) existing aliases, and a
    form to create a new aliases. When GET operation is used, both forms
    created and template is rendered. When POST operation is used, the form
    posted is detected using hidden form values and the appropriate form is
    initialized for the FormView base class to work with.
    """
    template_name = 'email-aliases.html'
    form_classes = (forms.AliasCreateForm, forms.AliasListForm)
    success_url = reverse_lazy('email:aliases')

    def __init__(self, *args, **kwargs):
        """Initialize the view."""
        super().__init__(*args, **kwargs)
        self.posted_form = None

    def get_form_class(self):
        """Return form class to build."""
        if self.posted_form == 'create':
            return forms.AliasCreateForm

        return forms.AliasListForm

    def get_form_kwargs(self):
        """Send aliases to list form."""
        kwargs = super().get_form_kwargs()
        if self.posted_form != 'create':
            kwargs['aliases'] = self._get_current_aliases()

        return kwargs

    def _get_current_aliases(self):
        """Return current list of aliases."""
        return aliases_module.get(self.request.user.username)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if isinstance(context['form'], forms.AliasCreateForm):
            context['create_form'] = context['form']
            aliases = self._get_current_aliases()
            context['list_form'] = forms.AliasListForm(aliases)
        else:
            context['create_form'] = forms.AliasCreateForm()
            context['list_form'] = context['form']

        return context

    def post(self, request, *args, **kwargs):
        """Find which form was submitted before proceeding."""
        self.posted_form = request.POST.get('form')
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle a valid submission."""
        if isinstance(form, forms.AliasListForm):
            self._list_form_valid(form)
        elif isinstance(form, forms.AliasCreateForm):
            self._create_form_valid(form)

        return super().form_valid(form)

    def _list_form_valid(self, form):
        """Handle a valid alias list form operation."""
        aliases = form.cleaned_data['aliases']
        username = self.request.user.username
        aliases_module.delete(username, aliases)

    def _create_form_valid(self, form):
        """Handle a valid create alias form operation."""
        username = self.request.user.username
        aliases_module.put(username, form.cleaned_data['alias'])


class XmlView(TemplateView):
    """Serve Thunderbird auto-configuration file.

    https://wiki.mozilla.org/Thunderbird:Autoconfiguration:ConfigFileFormat
    """
    template_name = 'email-autoconfig.xml'

    def render_to_response(self, *args, **kwargs):
        kwargs['content_type'] = 'text/xml; charset=utf-8'
        return super().render_to_response(*args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['host'] = self.request.get_host()
        return context
