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
Plinth module for configuring timezone, hostname etc.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import validators
from django.template.response import TemplateResponse
from gettext import gettext as _
import logging
import re
import socket

import actions
import cfg
import util


LOGGER = logging.getLogger(__name__)


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


class ConfigurationForm(forms.Form):
    """Main system configuration form"""
    time_zone = forms.ChoiceField(
        label=_('Time Zone'),
        help_text=_('Set your timezone to get accurate timestamps. \
This information will be used to set your systemwide timezone'))

    # We're more conservative than RFC 952 and RFC 1123
    hostname = TrimmedCharField(
        label=_('Hostname'),
        help_text=_('Your hostname is the local name by which other machines \
on your LAN can reach you. It must be alphanumeric, start with an alphabet \
and must not be greater than 63 characters in length.'),
        validators=[
            validators.RegexValidator(r'^[a-zA-Z][a-zA-Z0-9]{,62}$',
                                      _('Invalid hostname'))])

    def __init__(self, *args, **kwargs):
        # pylint: disable-msg=E1101, W0233
        forms.Form.__init__(self, *args, **kwargs)

        self.fields['time_zone'].choices = [(zone, zone)
                                            for zone in self.get_time_zones()]

    @staticmethod
    def get_time_zones():
        """Return list of available time zones"""
        time_zones = []
        for line in open('/usr/share/zoneinfo/zone.tab'):
            if re.match(r'^(#|\s*$)', line):
                continue

            try:
                time_zones.append(line.split()[2])
            except IndexError:
                pass

        time_zones.sort()
        return time_zones


def init():
    """Initialize the module"""
    menu = cfg.main_menu.get('system:index')
    menu.add_urlname(_('Configure'), 'icon-cog', 'config:index', 10)


@login_required
def index(request):
    """Serve the configuration form"""
    status = get_status()

    form = None

    is_expert = request.user.groups.filter(name='Expert').exists()
    if request.method == 'POST' and is_expert:
        form = ConfigurationForm(request.POST, prefix='configuration')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status()
            form = ConfigurationForm(initial=status,
                                     prefix='configuration')
    else:
        form = ConfigurationForm(initial=status, prefix='configuration')

    return TemplateResponse(request, 'config.html',
                            {'title': _('General Configuration'),
                             'form': form,
                             'is_expert': is_expert})


def get_status():
    """Return the current status"""
    return {'hostname': get_hostname(),
            'time_zone': util.slurp('/etc/timezone').rstrip()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    if old_status['hostname'] != new_status['hostname']:
        try:
            set_hostname(new_status['hostname'])
        except Exception as exception:
            messages.error(request, _('Error setting hostname: %s') %
                           str(exception))
        else:
            messages.success(request, _('Hostname set'))
    else:
        messages.info(request, _('Hostname is unchanged'))

    if old_status['time_zone'] != new_status['time_zone']:
        try:
            actions.superuser_run('timezone-change', [new_status['time_zone']])
        except Exception as exception:
            messages.error(request, _('Error setting time zone: %s') %
                           str(exception))
        else:
            messages.success(request, _('Time zone set'))
    else:
        messages.info(request, _('Time zone is unchanged'))


def set_hostname(hostname):
    """Sets machine hostname to hostname"""
    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert to ASCII.
    hostname = str(hostname)

    LOGGER.info('Changing hostname to - %s', hostname)
    actions.superuser_run('xmpp-pre-hostname-change')
    actions.superuser_run('hostname-change', hostname)
    actions.superuser_run('xmpp-hostname-change', hostname, async=True)
