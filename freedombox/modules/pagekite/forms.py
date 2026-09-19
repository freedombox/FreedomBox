# SPDX-License-Identifier: AGPL-3.0-or-later
"""Forms for configuring Pagekite."""

import copy

from django import forms
from django.contrib import messages
from django.core import validators
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from . import privileged, utils


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField."""

    def clean(self, value):
        """Clean and validate the field value."""
        if value:
            value = value.strip()

        return super().clean(value)


class ConfigurationForm(forms.Form):
    """Configure PageKite credentials and frontend."""

    server_domain = forms.CharField(
        label=gettext_lazy('Server domain'), required=False,
        help_text=gettext_lazy(
            'Select your pagekite server. Set "pagekite.net" to use '
            'the default pagekite.net server.'), widget=forms.TextInput())
    server_port = forms.IntegerField(
        label=gettext_lazy('Server port'), required=False,
        help_text=gettext_lazy('Port of your pagekite server (default: 80)'))
    kite_name = TrimmedCharField(
        label=gettext_lazy('Kite name'),
        help_text=gettext_lazy('Example: mybox.pagekite.me'), validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      gettext_lazy('Invalid kite name'))
        ])

    kite_secret = TrimmedCharField(
        label=gettext_lazy('Kite secret'), help_text=gettext_lazy(
            'A secret associated with the kite or the default secret '
            'for your account if no secret is set on the kite.'))

    def save(self, request):
        """Save the form on submission after validation."""

        def _filter(data):
            return {
                key: str(value)
                for key, value in data.items() if key in
                ['kite_name', 'kite_secret', 'server_domain', 'server_port']
            }

        if not self.cleaned_data['server_domain']:
            self.cleaned_data['server_domain'] = 'pagekite.net'

        if not self.cleaned_data['server_port']:
            self.cleaned_data['server_port'] = '80'

        old = _filter(self.initial)
        new = _filter(self.cleaned_data)

        # Let's Encrypt certificate paths use lower-case kite name.
        kite_name = new['kite_name'].lower()

        if old != new:
            frontend = f"{new['server_domain']}:{new['server_port']}"
            privileged.set_config(frontend, kite_name, new['kite_secret'])
            messages.success(request, _('Configuration updated'))

            # Update kite name registered with Name Services module.
            utils.update_names_module()


class BaseCustomServiceForm(forms.Form):
    """Basic form functionality to handle a custom service."""

    choices = [('http', 'http'), ('https', 'https'), ('raw', 'raw')]
    protocol = forms.ChoiceField(choices=choices,
                                 label=gettext_lazy('protocol'))
    frontend_port = forms.IntegerField(
        min_value=0, max_value=65535,
        label=gettext_lazy('external (frontend) port'), required=True)
    backend_port = forms.IntegerField(
        min_value=0, max_value=65535,
        label=gettext_lazy('internal (freedombox) port'))
    subdomains = forms.BooleanField(label=gettext_lazy('Enable Subdomains'),
                                    required=False)

    def convert_formdata_to_service(self, formdata):
        """Add information to make a service out of the form data."""
        # convert integers to str (to compare values with DEFAULT_SERVICES)
        for field in ('frontend_port', 'backend_port'):
            formdata[field] = str(formdata[field])

        # set kitename and kitesecret if not already set
        if 'kitename' not in formdata:
            if 'subdomains' in formdata and formdata['subdomains']:
                formdata['kitename'] = "*.%s" % utils.KITE_NAME
            else:
                formdata['kitename'] = utils.KITE_NAME
        if 'secret' not in formdata:
            formdata['secret'] = utils.KITE_SECRET

        # merge protocol and frontend_port back to one entry (protocol)
        if 'frontend_port' in formdata:
            if formdata['frontend_port'] not in formdata['protocol']:
                formdata['protocol'] = "%s/%s" % (formdata['protocol'],
                                                  formdata['frontend_port'])
        if 'backend_host' not in formdata:
            formdata['backend_host'] = utils.BACKEND_HOST

        return formdata


class DeleteCustomServiceForm(BaseCustomServiceForm):
    """Form to remove custom service."""

    def delete(self, request):
        service = self.convert_formdata_to_service(self.cleaned_data)
        privileged.remove_service(service)
        messages.success(request, _('Deleted custom service'))


class AddCustomServiceForm(BaseCustomServiceForm):
    """Adds the save() method and validation to not add predefined services."""

    def matches_predefined_service(self, formdata):
        """Return whether the user input matches a predefined service."""
        service = self.convert_formdata_to_service(formdata)
        match_found = False
        for predefined_service_obj in utils.PREDEFINED_SERVICES.values():
            # manually add the port to compare predefined with custom services
            # that's due to the (sometimes) implicit port in the configuration
            predefined_service = copy.copy(predefined_service_obj['params'])
            if predefined_service['protocol'] == 'http':
                predefined_service['protocol'] = 'http/80'
            elif predefined_service['protocol'] == 'https':
                predefined_service['protocol'] = 'https/443'

            # The formdata service has additional keys, so we can't compare
            # the dicts directly.
            # instead look whether predefined_service is a subset of service
            if all(service[k] == v for k, v in predefined_service.items()):
                match_found = True
                break
        return match_found

    def clean(self):
        cleaned_data = super().clean()
        try:
            is_predefined = self.matches_predefined_service(cleaned_data)
        except KeyError:
            is_predefined = False
        if is_predefined:
            msg = _('This service is already available as a standard service.')
            raise forms.ValidationError(msg)
        return cleaned_data

    def save(self, request):
        service = self.convert_formdata_to_service(self.cleaned_data)
        try:
            privileged.add_service(service)
            messages.success(request, _('Added custom service'))
        except Exception as exception:
            if "already exists" in str(exception):
                messages.error(request, _('This service already exists'))
            else:
                raise
