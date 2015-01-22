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

from gettext import gettext as _
import logging

from django import forms
from django.contrib import messages
from django.core import validators

from actions.pagekite_util import convert_service_to_string
from .util import PREDEFINED_SERVICES, _run, get_kite_details, KITE_NAME, \
    KITE_SECRET, BACKEND_HOST

LOGGER = logging.getLogger(__name__)


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigurationForm(forms.Form):
    """Configure PageKite credentials and frontend"""

    enabled = forms.BooleanField(label=_('Enable PageKite'),
                                 required=False)

    server = forms.CharField(
        label=_('Server'), required=False,
        help_text=_('Select your pagekite.net server. Set "pagekite.net" to '
                    'use the default pagekite.net server'),
        widget=forms.TextInput())

    kite_name = TrimmedCharField(
        label=_('Kite name'),
        help_text=_('Example: mybox1-myacc.pagekite.me'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid kite name'))])

    kite_secret = TrimmedCharField(
        label=_('Kite secret'),
        help_text=_('A secret associated with the kite or the default secret \
for your account if no secret is set on the kite'))

    def save(self, request):
        old = self.initial
        new = self.cleaned_data
        LOGGER.info('New status is - %s', new)

        if old != new:
            _run(['daemon', 'stop'])

        if old['enabled'] != new['enabled']:
            if new['enabled']:
                _run(['enable'])
                messages.success(request, _('PageKite enabled'))
            else:
                _run(['disable'])
                messages.success(request, _('PageKite disabled'))

        if old['kite_name'] != new['kite_name'] or \
                old['kite_secret'] != new['kite_secret']:
            _run(['set-kite', '--kite-name', new['kite_name'],
                  '--kite-secret', new['kite_secret']])
            messages.success(request, _('Kite details set'))

        if old['server'] != new['server']:
            server = new['server']
            if server in ('defaults', 'default', 'pagekite.net'):
                _run(['enable-pagekitenet-frontend'])
            else:
                _run(['set-frontend', server])
            messages.success(request, _('Pagekite server set'))

        if old != new:
            _run(['daemon', 'start'])


class DefaultServiceForm(forms.Form):
    """Creates a form out of PREDEFINED_SERVICES"""

    def __init__(self, *args, **kwargs):
        """Add the fields from PREDEFINED_SERVICES"""
        super(DefaultServiceForm, self).__init__(*args, **kwargs)
        kite = get_kite_details()
        for name, service in PREDEFINED_SERVICES.items():
            if name in ('http', 'https'):
                help_text = service['help_text'].format(kite['kite_name'])
            else:
                help_text = service['help_text']
            self.fields[name] = forms.BooleanField(label=service['label'],
                                                   help_text=help_text,
                                                   required=False)

    def save(self, request):
        formdata = self.cleaned_data
        for service_name in PREDEFINED_SERVICES.keys():
            if self.initial[service_name] != formdata[service_name]:
                service = PREDEFINED_SERVICES[service_name]['params']
                service_string = convert_service_to_string(service)
                if formdata[service_name]:
                    _run(['add-service', '--service', service_string])
                    messages.success(request, _('Service enabled: {name}')
                                     .format(name=service_name))
                else:
                    _run(['remove-service', '--service', service_string])
                    messages.success(request, _('Service disabled: {name}')
                                     .format(name=service_name))


class CustomServiceForm(forms.Form):
    """Form to add/delete a custom service"""
    choices = [("http", "http"), ("https", "https"), ("raw", "raw")]
    protocol = forms.ChoiceField(choices=choices, label="protocol")
    frontend_port = forms.IntegerField(min_value=0, max_value=65535,
                                       label="external (frontend) port")
    backend_port = forms.IntegerField(min_value=0, max_value=65535,
                                      label="internal (freedombox) port")
    subdomains = forms.BooleanField(label="Enable Subdomains", required=False)

    def convert_form_data_to_service_string(self, formdata):
        """Prepare the user form input for being passed on to the action

        1. add all information that a 'service' is expected to have
        2. convert the service to a service_string
        """
        # set kitename and kitesecret if not already set
        if 'kitename' not in formdata:
            if 'subdomains' in formdata and formdata['subdomains']:
                formdata['kitename'] = "*.%s" % KITE_NAME
            else:
                formdata['kitename'] = KITE_NAME
        if 'secret' not in formdata:
            formdata['secret'] = KITE_SECRET

        # merge protocol and frontend_port to one entry (protocol)
        if 'frontend_port' in formdata:
            if str(formdata['frontend_port']) not in formdata['protocol']:
                formdata['protocol'] = "%s/%s" % (formdata['protocol'],
                                                  formdata['frontend_port'])
        if 'backend_host' not in formdata:
            formdata['backend_host'] = BACKEND_HOST

        return convert_service_to_string(formdata)

    def save(self, request):
        service = self.convert_form_data_to_service_string(self.cleaned_data)
        _run(['add-service', '--service', service])
        messages.success(request, _('Added custom service'))

    def delete(self, request):
        service = self.convert_form_data_to_service_string(self.cleaned_data)
        _run(['remove-service', '--service', service])
        messages.success(request, _('Deleted custom service'))
