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
    menu.add_urlname('Dynamic DNS', 'glyphicon-comment', 'dynamicdns:index', 40)


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
    enabled = forms.BooleanField(label=_('Enable dynamicdns'),
                                 required=False)

    dynamicdns_server = TrimmedCharField(
        label=_('Server Address'),
        help_text=_('Example: gnudip.provider.org'),
        validators=[
            validators.RegexValidator(r'^[\w-]{1,63}(\.[\w-]{1,63})*$',
                                      _('Invalid server name'))])

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
                     when you created the account. If you left this field \
                     empty your password will be unchanged.'))

    dynamicdns_secret_repeat = TrimmedCharField(
        label=_('repeat Password'), widget=forms.PasswordInput(),
        required=False,
        help_text=_('insert the password twice to avoid typos. If you left \
                     this field empty your password will be unchanged.'),)

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


@login_required
@package.required('ez-ipupdate')
def configure(request):
    """Serve the configuration form"""
    status = get_status()
    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='dynamicdns')
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
    fail = False

    if new_status['dynamicdns_secret_repeat'] != \
       new_status['dynamicdns_secret']:

        messages.error(request, _('passwords does not match'))
        fail = True

    if old_status['dynamicdns_secret'] == '' and \
        new_status['dynamicdns_secret'] == '':
        messages.error(request, _('please give a password'))
        fail = True

    if False == fail:
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
           new_status['dynamicdns_ipurl']:

            _run(['configure', '-s', new_status['dynamicdns_server'],
                  '-d', new_status['dynamicdns_domain'],
                  '-u', new_status['dynamicdns_user'],
                  '-p', new_status['dynamicdns_secret'],
                  '-I', new_status['dynamicdns_ipurl']])
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
    command = 'dynamicdns'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
