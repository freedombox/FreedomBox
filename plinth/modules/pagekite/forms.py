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

import copy
from django import forms
from django.contrib import messages
from django.core import validators
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _, ugettext_lazy
import json
import logging

from . import utils
from plinth.errors import ActionError

LOGGER = logging.getLogger(__name__)


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""

    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class SubdomainWidget(forms.widgets.TextInput):
    """Append the domain to the subdomain bootstrap input field"""

    def __init__(self, domain, *args, **kwargs):
        """Initialize the widget by storing the domain value."""
        super().__init__(*args, **kwargs)
        self.domain = domain

    def render(self, *args, **kwargs):
        """Return the HTML for the widget."""
        inputfield = super().render(*args, **kwargs)
        return """<div class="input-group">
                  {0}
                  <span class="input-group-addon">{1}</span>
               </div>""".format(inputfield, self.domain)


class ConfigurationForm(forms.Form):
    """Configure PageKite credentials and frontend"""

    enabled = forms.BooleanField(
        label=ugettext_lazy('Enable PageKite'), required=False)

    server_domain = forms.CharField(
        label=ugettext_lazy('Server domain'), required=False,
        help_text=ugettext_lazy(
            'Select your pagekite server. Set "pagekite.net" to use '
            'the default pagekite.net server.'),
        widget=forms.TextInput())
    server_port = forms.IntegerField(
        label=ugettext_lazy('Server port'), required=False,
        help_text=ugettext_lazy('Port of your pagekite server (default: 80)'))
    kite_name = TrimmedCharField(
        label=ugettext_lazy('Kite name'),
        help_text=ugettext_lazy('Example: mybox.pagekite.me'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      ugettext_lazy('Invalid kite name'))])

    kite_secret = TrimmedCharField(
        label=ugettext_lazy('Kite secret'),
        help_text=ugettext_lazy(
            'A secret associated with the kite or the default secret '
            'for your account if no secret is set on the kite.'))

    def save(self, request):
        """Save the form on submission after validation."""
        old = self.initial
        new = self.cleaned_data
        LOGGER.info('New status is - %s', new)

        if old != new:
            config_changed = False

            if old['kite_name'] != new['kite_name'] or \
               old['kite_secret'] != new['kite_secret']:
                utils.run(['set-kite', '--kite-name', new['kite_name']],
                          input=new['kite_secret'].encode())
                messages.success(request, _('Kite details set'))
                config_changed = True

            if old['server_domain'] != new['server_domain'] or \
               old['server_port'] != new['server_port']:
                server = "%s:%s" % (new['server_domain'], new['server_port'])
                utils.run(['set-frontend', server])
                messages.success(request, _('Pagekite server set'))
                config_changed = True

            if old['enabled'] != new['enabled']:
                if new['enabled']:
                    utils.run(['start-and-enable'])
                    messages.success(request, _('PageKite enabled'))
                else:
                    utils.run(['stop-and-disable'])
                    messages.success(request, _('PageKite disabled'))

            # Restart the service if the config was changed while the service
            # was running, so changes take effect immediately.
            elif config_changed and new['enabled']:
                utils.run(['restart'])

            # Update kite name registered with Name Services module.
            utils.update_names_module(enabled=new['enabled'],
                                      kite_name=new['kite_name'])


class StandardServiceForm(forms.Form):
    """Creates a form out of PREDEFINED_SERVICES"""

    def __init__(self, *args, **kwargs):
        """Add the fields from PREDEFINED_SERVICES"""
        super(StandardServiceForm, self).__init__(*args, **kwargs)
        kite = utils.get_kite_details()
        for name, service in utils.PREDEFINED_SERVICES.items():
            if name in ('http', 'https'):
                help_text = service['help_text'].format(kite['kite_name'])
            else:
                help_text = service['help_text']
            self.fields[name] = forms.BooleanField(label=service['label'],
                                                   help_text=help_text,
                                                   required=False)

    def save(self, request):
        formdata = self.cleaned_data
        for service_name in utils.PREDEFINED_SERVICES.keys():
            if self.initial[service_name] != formdata[service_name]:
                service = utils.PREDEFINED_SERVICES[service_name]['params']
                service = json.dumps(service)
                if formdata[service_name]:
                    utils.run(['add-service', '--service', service])
                    messages.success(request, _('Service enabled: {name}')
                                     .format(name=service_name))
                else:
                    utils.run(['remove-service', '--service', service])
                    messages.success(request, _('Service disabled: {name}')
                                     .format(name=service_name))

        # Update kite services registered with Name Services module.
        utils.update_names_module()


class BaseCustomServiceForm(forms.Form):
    """Basic form functionality to handle a custom service"""
    choices = [('http', 'http'), ('https', 'https'), ('raw', 'raw')]
    protocol = forms.ChoiceField(
        choices=choices, label=ugettext_lazy('protocol'))
    frontend_port = forms.IntegerField(
        min_value=0, max_value=65535,
        label=ugettext_lazy('external (frontend) port'), required=True)
    backend_port = forms.IntegerField(
        min_value=0, max_value=65535,
        label=ugettext_lazy('internal (freedombox) port'))
    subdomains = forms.BooleanField(
        label=ugettext_lazy('Enable Subdomains'), required=False)

    def convert_formdata_to_service(self, formdata):
        """Add information to make a service out of the form data"""
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
        utils.run(['remove-service', '--service', json.dumps(service)])
        messages.success(request, _('Deleted custom service'))


class AddCustomServiceForm(BaseCustomServiceForm):
    """Adds the save() method and validation to not add predefined services"""

    def matches_predefined_service(self, formdata):
        """Returns whether the user input matches a predefined service"""
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
        cleaned_data = super(AddCustomServiceForm, self).clean()
        try:
            is_predefined = self.matches_predefined_service(cleaned_data)
        except KeyError:
            is_predefined = False
        if is_predefined:
            msg = _('This service is available as a standard service. Please '
                    'use the "Standard Services" page to enable it.')
            raise forms.ValidationError(msg)
        return cleaned_data

    def save(self, request):
        service = self.convert_formdata_to_service(self.cleaned_data)
        try:
            utils.run(['add-service', '--service', json.dumps(service)])
            messages.success(request, _('Added custom service'))
        except ActionError as exception:
            if "already exists" in str(exception):
                messages.error(request, _('This service already exists'))
            else:
                raise
