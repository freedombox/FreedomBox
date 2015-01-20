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

from actions.pagekite_util import deconstruct_params
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
            _run(['stop'])

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
            _run(['start'])


class DefaultServiceForm(forms.Form):
    """Constructs a form out of PREDEFINED_SERVICES"""

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
        for service in PREDEFINED_SERVICES.keys():
            if self.initial[service] != formdata[service]:
                params = PREDEFINED_SERVICES[service]['params']
                param_line = deconstruct_params(params)
                if formdata[service]:
                    _run(['add-service', '--params', param_line])
                    messages.success(request, _('Service enabled: {service}')
                                     .format(service=service))
                else:
                    _run(['remove-service', '--params', param_line])
                    messages.success(request, _('Service disabled: {service}')
                                     .format(service=service))


class CustomServiceForm(forms.Form):
    """Form to add/delete a custom service"""
    choices = [("http", "http"), ("https", "https"), ("raw", "raw")]
    protocol = forms.ChoiceField(choices=choices, label="Protocol")
    frontend_port = forms.IntegerField(min_value=0, max_value=65535,
                                       label="Frontend Port")
    backend_port = forms.IntegerField(min_value=0, max_value=65535,
                                      label="Local Port")
    subdomains = forms.BooleanField(label="Enable Subdomains", required=False)

    def prepare_user_input_for_storage(self, params):
        """prepare the user input for being stored via the action"""
        # set kitename and kitesecret if not already set
        if 'kitename' not in params:
            if 'subdomains' in params and params['subdomains']:
                params['kitename'] = "*.%s" % KITE_NAME
            else:
                params['kitename'] = KITE_NAME
        if 'secret' not in params:
            params['secret'] = KITE_SECRET

        # condense protocol and frontend_port to one entry (protocol)
        if 'frontend_port' in params:
            if str(params['frontend_port']) not in params['protocol']:
                params['protocol'] = "%s/%s" % (params['protocol'],
                                                params['frontend_port'])
        if 'backend_host' not in params:
            params['backend_host'] = BACKEND_HOST

        return deconstruct_params(params)

    def save(self, request):
        params = self.prepare_user_input_for_storage(self.cleaned_data)
        _run(['add-service', '--params', params])

    def delete(self, request):
        params = self.prepare_user_input_for_storage(self.cleaned_data)
        _run(['remove-service', '--params', params])
