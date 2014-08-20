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

"""
Plinth module for configuring PageKite service
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import validators
from django.core.urlresolvers import reverse_lazy
from django.template import RequestContext
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging

import actions
import cfg


LOGGER = logging.getLogger(__name__)


def init():
    """Intialize the PageKite module"""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(_('Public Visibility (PageKite)'), 'icon-flag',
                     'pagekite:index', 50)


@login_required
def index(request):
    """Serve introdution page"""
    menu = {'title': _('PageKite'),
            'items': [{'url': reverse_lazy('pagekite:configure'),
                       'text': _('Configure PageKite')}]}

    sidebar_right = render_to_string('menu_block.html', {'menu': menu},
                                     RequestContext(request))

    return TemplateResponse(request, 'pagekite_introduction.html',
                            {'title': _('Public Visibility (PageKite)'),
                             'sidebar_right': sidebar_right})


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigureForm(forms.Form):  # pylint: disable-msg=W0232
    """Form to configure PageKite"""
    enabled = forms.BooleanField(label=_('Enable PageKite'),
                                 required=False)

    server = forms.CharField(
        label=_('Server'), required=False,
        help_text=_('Currently only pagekite.net server is supported'),
        widget=forms.TextInput(attrs={'placeholder': 'pagekite.net',
                                      'disabled': 'disabled'}))

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

    http_enabled = forms.BooleanField(
        label=_('Web Server (HTTP)'), required=False,
        help_text=_('Site will be available at \
<a href="http://mybox1-myacc.pagekite.me">http://mybox1-myacc.pagekite.me \
</a>'))

    ssh_enabled = forms.BooleanField(
        label=_('Secure Shell (SSH)'), required=False,
        help_text=_('See SSH client setup <a href="\
https://pagekite.net/wiki/Howto/SshOverPageKite/">instructions</a>'))


@login_required
def configure(request):
    """Serve the configuration form"""
    status = get_status()

    form = None

    if request.method == 'POST':
        form = ConfigureForm(request.POST, prefix='pagekite')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigureForm(initial=status, prefix='pagekite')
    else:
        form = ConfigureForm(initial=status, prefix='pagekite')

    return TemplateResponse(request, 'pagekite_configure.html',
                            {'title': _('Configure PageKite'),
                             'form': form})


def get_status():
    """
    Return the current status of PageKite configuration by
    executing various actions.
    """
    status = {}

    # Check if PageKite is installed
    output = _run(['get-installed'])
    if output.split()[0] != 'installed':
        return None

    # PageKite service enabled/disabled
    output = _run(['get-status'])
    status['enabled'] = (output.split()[0] == 'enabled')

    # PageKite kite details
    output = _run(['get-kite'])
    kite_details = output.split()
    status['kite_name'] = kite_details[0]
    status['kite_secret'] = kite_details[1]

    # Service status
    status['service'] = {}
    for service in ('http', 'ssh'):
        output = _run(['get-service-status', service])
        status[service + '_enabled'] = (output.split()[0] == 'enabled')

    return status


def _apply_changes(request, old_status, new_status):
    """Apply the changes to PageKite configuration"""
    LOGGER.info('New status is - %s', new_status)

    if old_status != new_status:
        _run(['stop'])

    if old_status['enabled'] != new_status['enabled']:
        if new_status['enabled']:
            _run(['set-status', 'enable'])
            messages.success(request, _('PageKite enabled'))
        else:
            _run(['set-status', 'disable'])
            messages.success(request, _('PageKite disabled'))

    if old_status['kite_name'] != new_status['kite_name'] or \
            old_status['kite_secret'] != new_status['kite_secret']:
        _run(['set-kite', '--kite-name', new_status['kite_name'],
              '--kite-secret', new_status['kite_secret']])
        messages.success(request, _('Kite details set'))

    for service in ['http', 'ssh']:
        if old_status[service + '_enabled'] != \
                new_status[service + '_enabled']:
            if new_status[service + '_enabled']:
                _run(['set-service-status', service, 'enable'])
                messages.success(request, _('Service enabled: {service}')
                                 .format(service=service))
            else:
                _run(['set-service-status', service, 'disable'])
                messages.success(request, _('Service disabled: {service}')
                                 .format(service=service))

    if old_status != new_status:
        _run(['start'])


def _run(arguments, superuser=True):
    """Run an given command and raise exception if there was an error"""
    command = 'pagekite-configure'

    if superuser:
        return actions.superuser_run(command, arguments)
    else:
        return actions.run(command, arguments)
