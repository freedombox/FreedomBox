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

LOGGER = logging.getLogger(__name__)

subsubmenu = [{'url': reverse_lazy('dynamicDNS:index'),
               'text': _('About')},
              {'url': reverse_lazy('dynamicDNS:configure'),
               'text': _('Configure')},
              {'url': reverse_lazy('dynamicDNS:statuspage'),
               'text': _('Status')}
              ]


def init():
    """Initialize the dynamicDNS module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname('dynamicDNS', 'glyphicon-comment', 'dynamicDNS:index', 40)


@login_required
def index(request):
    """Serve dynamic DNS  page"""

    is_installed = actions.run('dynamicDNS', ['get-installed']).strip() \
                 == 'installed'

    if is_installed:
        index_subsubmenu = subsubmenu
    else:
        index_subsubmenu = None

    return TemplateResponse(request, 'dynamicDNS.html',
                            {'title': _('dynamicDNS'),
                             'is_installed': is_installed,
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
    enabled = forms.BooleanField(label=_('Enable dynamicDNS'),
                                 required=False)

    dynamicDNS_Server = TrimmedCharField(
        label=_('Server Address'),
        help_text=_('Example: gnudip.provider.org'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid server name'))])

    dynamicDNS_Domain = TrimmedCharField(
        label=_('Domain Name'),
        help_text=_('Example: hostname.sds-ip.de'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid domain name'))])

    dynamicDNS_User = TrimmedCharField(
        label=_('Username'),
        help_text=_('You should have been requested to select a username \
                     when you created the account'))

    dynamicDNS_Secret = TrimmedCharField(
        label=_('Password'), widget=forms.PasswordInput(),
        required=False,
        help_text=_('You should have been requested to select a password \
                     when you created the account. If you left this field \
                     empty your password will be unchanged.'))

    dynamicDNS_Secret_repeat = TrimmedCharField(
        label=_('repeat Password'), widget=forms.PasswordInput(),
        required=False,
        help_text=_('insert the password twice to avoid typos. If you left \
                     this field empty your password will be unchanged.'),)

    dynamicDNS_IPURL = TrimmedCharField(
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


@login_required
def configure(request):
    """Serve the configuration form"""
    status = get_status()
    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='dynamicDNS')
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='dynamicDNS')
    else:
        form = ConfigureForm(initial=status, prefix='dynamicDNS')

    return TemplateResponse(request, 'dynamicDNS_configure.html',
                            {'title': _('Configure dynamicDNS Client'),
                             'form': form,
                             'subsubmenu': subsubmenu})


@login_required
def statuspage(request):
    """Serve the status page """
    check_nat = actions.run('dynamicDNS', ['get-nat'])
    last_update = actions.run('dynamicDNS', ['get-last-success'])

    no_nat = check_nat.strip() == 'no'
    nat_unchecked = check_nat.strip() == 'unknown'
    timer = actions.run('dynamicDNS', ['get-timer'])

    if no_nat:
        LOGGER.info('we are not behind a NAT')

    if nat_unchecked:
        LOGGER.info('we did not checked if we are behind a NAT')

    return TemplateResponse(request, 'dynamicDNS_status.html',
                            {'title': _('Status of dynamicDNS Client'),
                             'no_nat': no_nat,
                             'nat_unchecked': nat_unchecked,
                             'timer': timer,
                             'last_update': last_update,
                             'subsubmenu': subsubmenu})


def get_status():
    """Return the current status"""
    """ToDo: use key/value instead of hard coded value list"""
    status = {}
    output = actions.run('dynamicDNS', 'status')
    details = output.split()
    status['enabled'] = (output.split()[0] == 'enabled')
    if len(details) > 1:
        status['dynamicDNS_Server'] = details[1]
    else:
        status['dynamicDNS_Server'] = ''

    if len(details) > 2:
        status['dynamicDNS_Domain'] = details[2]
    else:
        status['dynamicDNS_Domain'] = ''

    if len(details) > 3:
        status['dynamicDNS_User'] = details[3]
    else:
        status['dynamicDNS_User'] = ''

    if len(details) > 4:
        status['dynamicDNS_Secret'] = details[4]
    else:
        status['dynamicDNS_Secret'] = ''

    if len(details) > 5:
        status['dynamicDNS_IPURL'] = details[5]
    else:
        status['dynamicDNS_Secret'] = ''

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes to Dynamic DNS client"""
    LOGGER.info('New status is - %s', new_status)
    LOGGER.info('Old status was - %s', old_status)
    fail = False

    if new_status['dynamicDNS_Secret_repeat'] != \
       new_status['dynamicDNS_Secret']:

        messages.error(request, _('passwords does not match'))
        fail = True

    if old_status['dynamicDNS_Secret'] == '' and \
        new_status['dynamicDNS_Secret'] == '':
        messages.error(request, _('please give a password'))
        fail = True

    if False == fail:
        if new_status['dynamicDNS_Secret'] == '':
            new_status['dynamicDNS_Secret'] = old_status['dynamicDNS_Secret']

        if new_status['dynamicDNS_IPURL'] == '':
            new_status['dynamicDNS_IPURL'] = 'none'

        if old_status['dynamicDNS_Server'] != \
           new_status['dynamicDNS_Server'] or \
           old_status['dynamicDNS_Domain'] != \
           new_status['dynamicDNS_Domain'] or \
           old_status['dynamicDNS_User'] != \
           new_status['dynamicDNS_User'] or \
           old_status['dynamicDNS_Secret'] != \
           new_status['dynamicDNS_Secret'] or \
           old_status['dynamicDNS_IPURL'] != \
           new_status['dynamicDNS_IPURL']:

            _run(['configure', '-s', new_status['dynamicDNS_Server'],
                  '-d', new_status['dynamicDNS_Domain'],
                  '-u', new_status['dynamicDNS_User'],
                  '-p', new_status['dynamicDNS_Secret'],
                  '-I', new_status['dynamicDNS_IPURL']])
            _run(['stop'])
            _run(['start'])
            messages.success(request, \
            _('Dynamic DNS configuration is updated!'))

        if old_status['enabled'] != new_status['enabled']:
            if new_status['enabled']:
                _run(['start'])
                messages.success(request, _('Dynamic DNS is enabled now!'))
            else:
                _run(['stop'])
                messages.success(request, _('Dynamic DNS is disabled now!'))
    else:
        messages.error(request, \
        _('At least on failure occured, please check your input.'))


def _run(arguments, superuser=False):
    """Run a given command and raise exception if there was an error"""
    command = 'dynamicDNS'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
