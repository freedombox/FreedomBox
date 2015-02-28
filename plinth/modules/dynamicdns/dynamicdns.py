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
from django.contrib.auth.decorators import login_required
from django.core import validators
from django.core.urlresolvers import reverse_lazy
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

from plinth import actions
from plinth import cfg
from plinth import package

LOGGER = logging.getLogger(__name__)

subsubmenu = [{'url': reverse_lazy('dynamicdns:index'),
               'text': _('About')},
              {'url': reverse_lazy('dynamicdns:configure'),
               'text': _('Configure')},
              {'url': reverse_lazy('dynamicdns:statuspage'),
               'text': _('Status')}
              ]


def init():
    """Initialize the dynamicdns module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('Dynamic DNS', 'glyphicon-refresh',
                     'dynamicdns:index', 40)


@login_required
@package.required('ez-ipupdate')
def index(request):
    """Serve dynamic DNS  page"""

    index_subsubmenu = subsubmenu

    return TemplateResponse(request, 'dynamicdns.html',
                            {'title': _('dynamicdns'),
                             'subsubmenu': index_subsubmenu})


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigureForm(forms.Form):
    """Form to configure the dynamic DNS client"""
    enabled = forms.BooleanField(label=_('Enable Dynamic DNS'),
                                 required=False)

    dynamicdns_service = forms.ChoiceField(label=_('Service type'),
       help_text=_('Please choose a update protocol according to your provider.\
                   We recommend the GnudIP protocol. If your provider does not \
                   support the GnudIP protocol or your provider is not listed \
                   you may use the update URL of your provider.'),
                   choices=(('1', 'GnudIP'), 
                            ('2', 'noip.com'),
                            ('3', 'selfhost.bz'),
                            ('4', 'other Update URL')))

    dynamicdns_server = TrimmedCharField(
        label=_('GnudIP Server Address'),
        help_text=_('Example: gnudip.provider.org'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid server name'))])
    
    dynamicdns_update_url = TrimmedCharField(
         label=_('Update URL'),
         required=False,
         help_text=_('The Variables $User, $Pass, $IP, $Domain may be used \
                within this URL.</br> Example URL: </br> \
                https://some.tld/up.php?us=$User&pw=$Pass&ip=$IP&dom=$Domain'),
    validators=[
        validators.URLValidator(schemes=['http', 'https'])])
    
    disable_SSL_cert_check = forms.BooleanField(
                            label=_('accept all SSL certificates'),
                            help_text=_('use this option if your provider uses\
                            self signed certificates'),
                            required=False)
    
    use_http_basic_auth = forms.BooleanField(
                            label=_('use HTTP basic authentication'),
                            required=False)

    dynamicdns_domain = TrimmedCharField(
        label=_('Domain Name'),
        help_text=_('Example: hostname.sds-ip.de'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid domain name'))])

    dynamicdns_user = TrimmedCharField(
        label=_('Username'),
        help_text=_('You should have been requested to select a username \
                     when you created the account'))

    dynamicdns_secret = TrimmedCharField(
        label=_('Password'), widget=forms.PasswordInput(),
        required=False,
        help_text=_('You should have been requested to select a password \
                     when you created the account. Leave this field empty \
                     if you want to keep your previous configured password.'))

    showpw = forms.BooleanField(label=_('show password'),
                                required=False,
                                widget=forms.CheckboxInput
                                (attrs={'onclick': 'show_pass();'}))

    dynamicdns_ipurl = TrimmedCharField(
        label=_('IP check URL'),
        required=False,
        help_text=_('Optional Value. If your FreedomBox is not connected \
                     directly to the Internet (i.e. connected to a NAT \
                     router) this URL is used to figure out the real Internet \
                     IP. The URL should simply return the IP where the \
                     client comes from. Example: \
                     http://myip.datasystems24.de'),
        validators=[
            validators.URLValidator(schemes=['http', 'https', 'ftp'])])

    def clean(self):
        cleaned_data = super(ConfigureForm, self).clean()
        dynamicdns_secret = cleaned_data.get("dynamicdns_secret")
        old_dynamicdns_secret = self.initial['dynamicdns_secret']

        if not dynamicdns_secret and not old_dynamicdns_secret:
            raise forms.ValidationError("please give a password")


@login_required
@package.required('ez-ipupdate')
def configure(request):
    """Serve the configuration form"""
    status = get_status()
    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, initial=status, prefix='dynamicdns')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='dynamicdns')
    else:
        form = ConfigureForm(initial=status, prefix='dynamicdns')

    return TemplateResponse(request, 'dynamicdns_configure.html',
                            {'title': _('Configure dynamicdns Client'),
                             'form': form,
                             'subsubmenu': subsubmenu})


@login_required
@package.required('ez-ipupdate')
def statuspage(request):
    """Serve the status page """
    check_nat = actions.run('dynamicdns', ['get-nat'])
    last_update = actions.run('dynamicdns', ['get-last-success'])

    no_nat = check_nat.strip() == 'no'
    nat_unchecked = check_nat.strip() == 'unknown'
    timer = actions.run('dynamicdns', ['get-timer'])

    if no_nat:
        LOGGER.info('we are not behind a NAT')

    if nat_unchecked:
        LOGGER.info('we did not checked if we are behind a NAT')

    return TemplateResponse(request, 'dynamicdns_status.html',
                            {'title': _('Status of dynamicdns Client'),
                             'no_nat': no_nat,
                             'nat_unchecked': nat_unchecked,
                             'timer': timer,
                             'last_update': last_update,
                             'subsubmenu': subsubmenu})


def get_status():
    """Return the current status"""
    """ToDo: use key/value instead of hard coded value list"""
    status = {}
    output = actions.run('dynamicdns', 'status')
    details = output.split()
    status['enabled'] = (output.split()[0] == 'enabled')
    if len(details) > 1:
        status['dynamicdns_server'] = details[1]
    else:
        status['dynamicdns_server'] = ''

    if len(details) > 2:
        status['dynamicdns_domain'] = details[2]
    else:
        status['dynamicdns_domain'] = ''

    if len(details) > 3:
        status['dynamicdns_user'] = details[3]
    else:
        status['dynamicdns_user'] = ''

    if len(details) > 4:
        status['dynamicdns_secret'] = details[4]
    else:
        status['dynamicdns_secret'] = ''

    if len(details) > 5:
        status['dynamicdns_ipurl'] = details[5]
    else:
        status['dynamicdns_secret'] = ''

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes to Dynamic DNS client"""
    LOGGER.info('New status is - %s', new_status)
    LOGGER.info('Old status was - %s', old_status)

    if new_status['dynamicdns_secret'] == '':
        new_status['dynamicdns_secret'] = old_status['dynamicdns_secret']

    if new_status['dynamicdns_ipurl'] == '':
        new_status['dynamicdns_ipurl'] = 'none'

    if old_status['dynamicdns_server'] != \
       new_status['dynamicdns_server'] or \
       old_status['dynamicdns_domain'] != \
       new_status['dynamicdns_domain'] or \
       old_status['dynamicdns_user'] != \
       new_status['dynamicdns_user'] or \
       old_status['dynamicdns_secret'] != \
       new_status['dynamicdns_secret'] or \
       old_status['dynamicdns_ipurl'] != \
       new_status['dynamicdns_ipurl'] or \
       old_status['enabled'] != \
       new_status['enabled']:

        _run(['configure', '-s', new_status['dynamicdns_server'],
              '-d', new_status['dynamicdns_domain'],
              '-u', new_status['dynamicdns_user'],
              '-p', new_status['dynamicdns_secret'],
              '-I', new_status['dynamicdns_ipurl']])

        if old_status['enabled']:
            _run(['stop'])
        if new_status['enabled']:
            _run(['start'])

        messages.success(request,
                         _('Dynamic DNS configuration is updated!'))


def _run(arguments, superuser=False):
    """Run a given command and raise exception if there was an error"""
    command = 'dynamicdns'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
