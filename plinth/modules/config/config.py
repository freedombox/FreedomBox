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

from plinth import actions
from plinth import cfg
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change


LOGGER = logging.getLogger(__name__)


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


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

    domainname = TrimmedCharField(
        label=_('Domain Name'),
        help_text=_('Your domain name is the global name by which other \
machines on the Internet can reach you. It must consist of alphanumeric words \
separated by dots.'),
        required=False,
        validators=[
            validators.RegexValidator(r'^[a-zA-Z][a-zA-Z0-9.]*$',
                                      _('Invalid domain name'))])

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
    menu.add_urlname(_('Configure'), 'glyphicon-cog', 'config:index', 10)


@login_required
def index(request):
    """Serve the configuration form"""
    status = get_status()

    form = None

    if request.method == 'POST':
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
                             'form': form})


def get_status():
    """Return the current status"""
    return {'hostname': get_hostname(),
            'domainname': get_domainname(),
            'time_zone': open('/etc/timezone').read().rstrip()}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    if old_status['hostname'] != new_status['hostname']:
        try:
            set_hostname(new_status['hostname'])
        except Exception as exception:
            messages.error(request, _('Error setting hostname: %s') %
                           exception)
        else:
            messages.success(request, _('Hostname set'))
    else:
        messages.info(request, _('Hostname is unchanged'))

    if old_status['domainname'] != new_status['domainname']:
        try:
            set_domainname(new_status['domainname'])
        except Exception as exception:
            messages.error(request, _('Error setting domain name: %s') %
                           exception)
        else:
            messages.success(request, _('Domain name set'))
    else:
        messages.info(request, _('Domain name is unchanged'))

    if old_status['time_zone'] != new_status['time_zone']:
        try:
            actions.superuser_run('timezone-change', [new_status['time_zone']])
        except Exception as exception:
            messages.error(request, _('Error setting time zone: %s') %
                           exception)
        else:
            messages.success(request, _('Time zone set'))
    else:
        messages.info(request, _('Time zone is unchanged'))


def set_hostname(hostname):
    """Sets machine hostname to hostname"""
    old_hostname = get_hostname()

    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert to ASCII.
    hostname = str(hostname)

    pre_hostname_change.send_robust(sender='config',
                                    old_hostname=old_hostname,
                                    new_hostname=hostname)

    LOGGER.info('Changing hostname to - %s', hostname)
    actions.superuser_run('hostname-change', [hostname])

    post_hostname_change.send_robust(sender='config',
                                     old_hostname=old_hostname,
                                     new_hostname=hostname)


def set_domainname(domainname):
    """Sets machine domain name to domainname"""
    old_domainname = get_domainname()

    # Domain name should be ASCII. If it's unicode, convert to ASCII.
    domainname = str(domainname)

    LOGGER.info('Changing domain name to - %s', domainname)
    actions.superuser_run('domainname-change', [domainname])

    domainname_change.send_robust(sender='config',
                                  old_domainname=old_domainname,
                                  new_domainname=domainname)
