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

from django import forms
from django.contrib import messages
from django.core import validators
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _, ugettext_lazy
from django.template.response import TemplateResponse
import logging

from plinth import actions
from plinth import cfg
from plinth.modules import dynamicdns
from plinth.utils import format_lazy

logger = logging.getLogger(__name__)
EMPTYSTRING = 'none'

subsubmenu = [{'url': reverse_lazy('dynamicdns:index'),
               'text': ugettext_lazy('About')},
              {'url': reverse_lazy('dynamicdns:configure'),
               'text': ugettext_lazy('Configure')},
              {'url': reverse_lazy('dynamicdns:statuspage'),
               'text': ugettext_lazy('Status')}]


def index(request):
    """Serve Dynamic DNS page."""
    return TemplateResponse(request, 'dynamicdns.html',
                            {'title': dynamicdns.title,
                             'description': dynamicdns.description,
                             'subsubmenu': subsubmenu})


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField."""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigureForm(forms.Form):
    """Form to configure the Dynamic DNS client."""
    help_update_url = \
        ugettext_lazy('The Variables &lt;User&gt;, &lt;Pass&gt;, &lt;Ip&gt;, '
                      '&lt;Domain&gt; may be used within the URL. For details '
                      'see the update URL templates of the example providers.')
    help_services = \
        ugettext_lazy('Please choose an update protocol according to your '
                      'provider. If your provider does not support the GnuDIP '
                      'protocol or your provider is not listed you may use the '
                      'update URL of your provider.')
    help_server = \
        ugettext_lazy('Please do not enter a URL here (like '
                      '"https://example.com/") but only the hostname of the '
                      'GnuDIP server (like "example.com").')
    help_domain = format_lazy(
        ugettext_lazy('The public domain name you want to use to reach your '
                      '{box_name}.'), box_name=ugettext_lazy(cfg.box_name))
    help_disable_ssl = \
        ugettext_lazy('Use this option if your provider uses self signed '
                      'certificates.')
    help_http_auth = \
        ugettext_lazy('If this option is selected, your username and password '
                      'will be used for HTTP basic authentication.')
    help_secret = \
        ugettext_lazy('Leave this field empty if you want to keep your '
                      'current password.')
    help_ip_url = format_lazy(
        ugettext_lazy('Optional Value. If your {box_name} is not connected '
                      'directly to the Internet (i.e. connected to a NAT '
                      'router) this URL is used to determine the real '
                      'IP address. The URL should simply return the IP where '
                      'the client comes from (example: '
                      'http://myip.datasystems24.de).'),
        box_name=ugettext_lazy(cfg.box_name))
    help_user = \
        ugettext_lazy('The username that was used when the account was '
                      'created.')

    """ToDo: sync this list with the html template file"""
    provider_choices = (
        ('GnuDIP', 'GnuDIP'),
        ('noip', 'noip.com'),
        ('selfhost', 'selfhost.bz'),
        ('freedns', 'freedns.afraid.org'),
        ('other', 'other update URL'))

    enabled = forms.BooleanField(label=ugettext_lazy('Enable Dynamic DNS'),
                                 required=False)

    service_type = forms.ChoiceField(label=ugettext_lazy('Service Type'),
                                     help_text=help_services,
                                     choices=provider_choices)

    dynamicdns_server = TrimmedCharField(
        label=ugettext_lazy('GnuDIP Server Address'),
        required=False,
        help_text=help_server,
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      ugettext_lazy('Invalid server name'))])

    dynamicdns_update_url = TrimmedCharField(
        label=ugettext_lazy('Update URL'), required=False,
        help_text=help_update_url)

    disable_SSL_cert_check = forms.BooleanField(
        label=ugettext_lazy('Accept all SSL certificates'),
        help_text=help_disable_ssl, required=False)

    use_http_basic_auth = forms.BooleanField(
        label=ugettext_lazy('Use HTTP basic authentication'),
        help_text=help_http_auth, required=False)

    dynamicdns_domain = TrimmedCharField(
        label=ugettext_lazy('Domain Name'),
        help_text=help_domain,
        required=False,
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      ugettext_lazy('Invalid domain name'))])

    dynamicdns_user = TrimmedCharField(
        label=ugettext_lazy('Username'), required=False, help_text=help_user)

    dynamicdns_secret = TrimmedCharField(
        label=ugettext_lazy('Password'), widget=forms.PasswordInput(),
        required=False, help_text=help_secret)

    showpw = forms.BooleanField(label=ugettext_lazy('Show password'),
                                required=False)

    dynamicdns_ipurl = TrimmedCharField(
        label=ugettext_lazy('URL to look up public IP'),
        required=False,
        help_text=help_ip_url,
        validators=[
            validators.URLValidator(schemes=['http', 'https', 'ftp'])])

    def clean(self):
        cleaned_data = super(ConfigureForm, self).clean()
        dynamicdns_secret = cleaned_data.get('dynamicdns_secret')
        dynamicdns_update_url = cleaned_data.get('dynamicdns_update_url')
        dynamicdns_user = cleaned_data.get('dynamicdns_user')
        dynamicdns_domain = cleaned_data.get('dynamicdns_domain')
        dynamicdns_server = cleaned_data.get('dynamicdns_server')
        service_type = cleaned_data.get('service_type')
        old_dynamicdns_secret = self.initial['dynamicdns_secret']

        # Clear the fields which are not in use
        if service_type == 'GnuDIP':
            dynamicdns_update_url = ''
        else:
            dynamicdns_server = ''

        if cleaned_data.get('enabled'):
            # Check if gnudip server or update URL is filled
            if not dynamicdns_update_url and not dynamicdns_server:
                raise forms.ValidationError(
                    _('Please provide an update URL or a GnuDIP server '
                      'address'))

            if dynamicdns_server and not dynamicdns_user:
                raise forms.ValidationError(
                    _('Please provide a GnuDIP username'))

            if dynamicdns_server and not dynamicdns_domain:
                raise forms.ValidationError(
                    _('Please provide a GnuDIP domain name'))

            # Check if a password was set before or a password is set now
            if dynamicdns_server and \
               not dynamicdns_secret and not old_dynamicdns_secret:
                raise forms.ValidationError(_('Please provide a password'))


def configure(request):
    """Serve the configuration form."""
    status = get_status()
    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, initial=status)
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status)
    else:
        form = ConfigureForm(initial=status)

    return TemplateResponse(request, 'dynamicdns_configure.html',
                            {'title': _('Configure Dynamic DNS'),
                             'form': form,
                             'subsubmenu': subsubmenu})


def statuspage(request):
    """Serve the status page."""
    check_nat = _run(['get-nat'])
    last_update = _run(['get-last-success'])

    no_nat = check_nat.strip() == 'no'
    nat_unchecked = check_nat.strip() == 'unknown'
    timer = _run(['get-timer'])

    if no_nat:
        logger.info('Not behind a NAT')

    if nat_unchecked:
        logger.info('Did not check if behind a NAT')

    return TemplateResponse(request, 'dynamicdns_status.html',
                            {'title': _('Dynamic DNS Status'),
                             'no_nat': no_nat,
                             'nat_unchecked': nat_unchecked,
                             'timer': timer,
                             'last_update': last_update,
                             'subsubmenu': subsubmenu})


def get_status():
    """Return the current status."""
    # TODO: use key/value instead of hard coded value list
    status = {}
    output = _run(['status'])
    details = output.split()
    status['enabled'] = (output.split()[0] == 'enabled')

    if len(details) > 1:
        if details[1] == 'disabled':
            status['dynamicdns_server'] = ''
        else:
            status['dynamicdns_server'] = details[1].replace("'", "")
    else:
        status['dynamicdns_server'] = ''

    if len(details) > 2:
        if details[2] == 'disabled':
            status['dynamicdns_domain'] = ''
        else:
            status['dynamicdns_domain'] = details[2].replace("'", "")
    else:
        status['dynamicdns_domain'] = ''

    if len(details) > 3:
        if details[3] == 'disabled':
            status['dynamicdns_user'] = ''
        else:
            status['dynamicdns_user'] = details[3].replace("'", "")
    else:
        status['dynamicdns_user'] = ''

    if len(details) > 4:
        if details[4] == 'disabled':
            status['dynamicdns_secret'] = ''
        else:
            status['dynamicdns_secret'] = details[4].replace("'", "")
    else:
        status['dynamicdns_secret'] = ''

    if len(details) > 5:
        if details[5] == 'disabled':
            status['dynamicdns_ipurl'] = ''
        else:
            status['dynamicdns_ipurl'] = details[5].replace("'", "")
    else:
        status['dynamicdns_ipurl'] = ''

    if len(details) > 6:
        if details[6] == 'disabled':
            status['dynamicdns_update_url'] = ''
        else:
            status['dynamicdns_update_url'] = details[6].replace("'", "")
    else:
        status['dynamicdns_update_url'] = ''

    if len(details) > 7:
        status['disable_SSL_cert_check'] = (output.split()[7] == 'enabled')
    else:
        status['disable_SSL_cert_check'] = False

    if len(details) > 8:
        status['use_http_basic_auth'] = (output.split()[8] == 'enabled')
    else:
        status['use_http_basic_auth'] = False

    if not status['dynamicdns_server'] and not status['dynamicdns_update_url']:
        status['service_type'] = 'GnuDIP'
    elif not status['dynamicdns_server'] and status['dynamicdns_update_url']:
        status['service_type'] = 'other'
    else:
        status['service_type'] = 'GnuDIP'

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes to Dynamic DNS client."""
    logger.info('New status is - %s', new_status)
    logger.info('Old status was - %s', old_status)

    if new_status['dynamicdns_secret'] == '':
        new_status['dynamicdns_secret'] = old_status['dynamicdns_secret']

    if new_status['dynamicdns_ipurl'] == '':
        new_status['dynamicdns_ipurl'] = EMPTYSTRING

    if new_status['dynamicdns_update_url'] == '':
        new_status['dynamicdns_update_url'] = EMPTYSTRING

    if new_status['dynamicdns_server'] == '':
        new_status['dynamicdns_server'] = EMPTYSTRING

    if new_status['service_type'] == 'GnuDIP':
        new_status['dynamicdns_update_url'] = EMPTYSTRING
    else:
        new_status['dynamicdns_server'] = EMPTYSTRING

    if old_status != new_status:
        disable_ssl_check = "disabled"
        use_http_basic_auth = "disabled"

        if new_status['disable_SSL_cert_check']:
            disable_ssl_check = "enabled"

        if new_status['use_http_basic_auth']:
            use_http_basic_auth = "enabled"

        _run(['configure', '-s', new_status['dynamicdns_server'],
              '-d', new_status['dynamicdns_domain'],
              '-u', new_status['dynamicdns_user'],
              '-p',
              '-I', new_status['dynamicdns_ipurl'],
              '-U', new_status['dynamicdns_update_url'],
              '-c', disable_ssl_check,
              '-b', use_http_basic_auth],
             input=new_status['dynamicdns_secret'].encode())

        if old_status['enabled']:
            _run(['stop'])

        if new_status['enabled']:
            _run(['start'])

        messages.success(request, _('Configuration updated'))
    else:
        logger.info('Nothing changed')


def _run(arguments, input=None):
    """Run a given command and raise exception if there was an error."""
    return actions.superuser_run('dynamicdns', arguments, input=input)
