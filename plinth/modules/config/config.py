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
Plinth module for configuring hostname and domainname.
"""

from django import forms
from django.contrib import messages
from django.core import validators
from django.core.exceptions import ValidationError
from django.conf import settings
from django.template.response import TemplateResponse
from django.utils import translation
from django.utils.translation import ugettext as _, ugettext_lazy
import logging
import os
import re
import socket

import plinth
from plinth import actions
from plinth import cfg
from plinth.menu import main_menu
from plinth.modules import firewall
from plinth.modules.names import SERVICES
from plinth.signals import pre_hostname_change, post_hostname_change
from plinth.signals import domainname_change
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy


HOSTNAME_REGEX = r'^[a-zA-Z0-9]([-a-zA-Z0-9]{,61}[a-zA-Z0-9])?$'

LOGGER = logging.getLogger(__name__)


def get_hostname():
    """Return the hostname"""
    return socket.gethostname()


def get_domainname():
    """Return the domainname"""
    fqdn = socket.getfqdn()
    return '.'.join(fqdn.split('.')[1:])


def get_language(request):
    """Return the current language setting"""
    # TODO: Store the language per user in kvstore,
    # taking care of setting language on login, and adapting kvstore when
    # renaming/deleting users

    # The information from the session is more accurate but not always present
    return request.session.get(translation.LANGUAGE_SESSION_KEY,
                               request.LANGUAGE_CODE)


class TrimmedCharField(forms.CharField):
    """Trim the contents of a CharField"""
    def clean(self, value):
        """Clean and validate the field value"""
        if value:
            value = value.strip()

        return super(TrimmedCharField, self).clean(value)


def domain_label_validator(domainname):
    """Validate domain name labels."""
    for label in domainname.split('.'):
        if not re.match(HOSTNAME_REGEX, label):
            raise ValidationError(_('Invalid domain name'))


class ConfigurationForm(forms.Form):
    """Main system configuration form"""
    # See:
    # https://tools.ietf.org/html/rfc952
    # https://tools.ietf.org/html/rfc1035#section-2.3.1
    # https://tools.ietf.org/html/rfc1123#section-2
    # https://tools.ietf.org/html/rfc2181#section-11
    hostname = TrimmedCharField(
        label=ugettext_lazy('Hostname'),
        help_text=format_lazy(ugettext_lazy(
            'Hostname is the local name by which other devices on the local '
            'network can reach your {box_name}.  It must start and end with '
            'an alphabet or a digit and have as interior characters only '
            'alphabets, digits and hyphens.  Total length must be 63 '
            'characters or less.'), box_name=ugettext_lazy(cfg.box_name)),
        validators=[
            validators.RegexValidator(
                HOSTNAME_REGEX,
                ugettext_lazy('Invalid hostname'))])

    domainname = TrimmedCharField(
        label=ugettext_lazy('Domain Name'),
        help_text=format_lazy(ugettext_lazy(
            'Domain name is the global name by which other devices on the '
            'Internet can reach your {box_name}.  It must consist of labels '
            'separated by dots.  Each label must start and end with an '
            'alphabet or a digit and have as interior characters only '
            'alphabets, digits and hyphens.  Length of each label must be 63 '
            'characters or less.  Total length of domain name must be 253 '
            'characters or less.'), box_name=ugettext_lazy(cfg.box_name)),
        required=False,
        validators=[
            validators.RegexValidator(
                r'^[a-zA-Z0-9]([-a-zA-Z0-9.]{,251}[a-zA-Z0-9])?$',
                ugettext_lazy('Invalid domain name')),
            domain_label_validator])

    language = forms.ChoiceField(
        label=ugettext_lazy('Language'),
        help_text=ugettext_lazy(
            'Language for this web administration interface'),
        required=False)

    def __init__(self, *args, **kwargs):
        """Set limited language choices."""
        super().__init__(*args, **kwargs)
        languages = []
        for language_code, language_name in settings.LANGUAGES:
            locale_code = translation.to_locale(language_code)
            plinth_dir = os.path.dirname(plinth.__file__)
            if language_code == 'en' or os.path.exists(
                    os.path.join(plinth_dir, 'locale', locale_code)):
                languages.append((language_code, language_name))

        self.fields['language'].choices = languages


def init():
    """Initialize the module"""
    menu = main_menu.get('system')
    menu.add_urlname(ugettext_lazy('Configure'), 'glyphicon-cog',
                     'config:index')

    # Register domain with Name Services module.
    domainname = get_domainname()
    if domainname:
        try:
            domainname_services = firewall.get_enabled_services(
                zone='external')
        except actions.ActionError:
            # This happens when firewalld is not installed.
            # TODO: Are these services actually enabled?
            domainname_services = [service[0] for service in SERVICES]
    else:
        domainname_services = None

    domain_added.send_robust(sender='config', domain_type='domainname',
                             name=domainname,
                             description=ugettext_lazy('Domain Name'),
                             services=domainname_services)


def index(request):
    """Serve the configuration form"""
    status = get_status(request)

    form = None

    if request.method == 'POST':
        form = ConfigurationForm(request.POST, initial=status,
                                 prefix='configuration')
        # pylint: disable-msg=E1101
        if form.is_valid():
            _apply_changes(request, status, form.cleaned_data)
            status = get_status(request)
            form = ConfigurationForm(initial=status,
                                     prefix='configuration')
    else:
        form = ConfigurationForm(initial=status, prefix='configuration')

    return TemplateResponse(request, 'config.html',
                            {'title': _('General Configuration'),
                             'form': form})


def get_status(request):
    """Return the current status"""
    return {'hostname': get_hostname(),
            'domainname': get_domainname(),
            'language': get_language(request)}


def _apply_changes(request, old_status, new_status):
    """Apply the form changes"""
    if old_status['hostname'] != new_status['hostname']:
        try:
            set_hostname(new_status['hostname'])
        except Exception as exception:
            messages.error(request, _('Error setting hostname: {exception}')
                           .format(exception=exception))
        else:
            messages.success(request, _('Hostname set'))

    if old_status['domainname'] != new_status['domainname']:
        try:
            set_domainname(new_status['domainname'])
        except Exception as exception:
            messages.error(request, _('Error setting domain name: {exception}')
                           .format(exception=exception))
        else:
            messages.success(request, _('Domain name set'))

    if old_status['language'] != new_status['language']:
        language = new_status['language']
        try:
            translation.activate(language)
            request.session[translation.LANGUAGE_SESSION_KEY] = language
        except Exception as exception:
            messages.error(request, _('Error setting language: {exception}')
                           .format(exception=exception))
        else:
            messages.success(request, _('Language changed'))


def set_hostname(hostname):
    """Sets machine hostname to hostname"""
    old_hostname = get_hostname()
    domainname = get_domainname()

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

    LOGGER.info('Setting domain name after hostname change - %s', domainname)
    actions.superuser_run('domainname-change', [domainname])


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

    # Update domain registered with Name Services module.
    domain_removed.send_robust(sender='config', domain_type='domainname')
    if domainname:
        try:
            domainname_services = firewall.get_enabled_services(
                zone='external')
        except actions.ActionError:
            # This happens when firewalld is not installed.
            # TODO: Are these services actually enabled?
            domainname_services = [service[0] for service in SERVICES]

        domain_added.send_robust(sender='config', domain_type='domainname',
                                 name=domainname, description=_('Domain Name'),
                                 services=domainname_services)
