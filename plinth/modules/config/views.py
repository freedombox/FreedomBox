#
# This file is part of FreedomBox.
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
FreedomBox views for basic system configuration.
"""

import logging

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import config
from plinth.signals import (domain_added, domain_removed, post_hostname_change,
                            pre_hostname_change)

from .forms import ConfigurationForm

LOGGER = logging.getLogger(__name__)


class ConfigAppView(views.AppView):
    """Serve configuration page."""
    form_class = ConfigurationForm
    app_id = 'config'
    show_status_block = False

    def get_initial(self):
        """Return the current status"""
        return {
            'hostname': config.get_hostname(),
            'domainname': config.get_domainname(),
            'homepage': config.get_home_page(),
            'advanced_mode': config.get_advanced_mode(),
        }

    def form_valid(self, form):
        """Apply the form changes"""
        old_status = form.initial
        new_status = form.cleaned_data

        if old_status['hostname'] != new_status['hostname']:
            try:
                set_hostname(new_status['hostname'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting hostname: {exception}').format(
                        exception=exception))
            else:
                messages.success(self.request, _('Hostname set'))

        if old_status['domainname'] != new_status['domainname']:
            try:
                set_domainname(new_status['domainname'],
                               old_status['domainname'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting domain name: {exception}').format(
                        exception=exception))
            else:
                messages.success(self.request, _('Domain name set'))

        if old_status['homepage'] != new_status['homepage']:
            try:
                config.change_home_page(new_status['homepage'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error setting webserver home page: {exception}').format(
                        exception=exception))
            else:
                messages.success(self.request, _('Webserver home page set'))

        if old_status['advanced_mode'] != new_status['advanced_mode']:
            try:
                config.set_advanced_mode(new_status['advanced_mode'])
            except Exception as exception:
                messages.error(
                    self.request,
                    _('Error changing advanced mode: {exception}').format(
                        exception=exception))
            else:
                if new_status['advanced_mode']:
                    messages.success(self.request,
                                     _('Showing advanced apps and features'))
                else:
                    messages.success(self.request,
                                     _('Hiding advanced apps and features'))

        return super(views.AppView, self).form_valid(form)


def set_hostname(hostname):
    """Sets machine hostname to hostname"""
    old_hostname = config.get_hostname()
    domainname = config.get_domainname()

    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert
    hostname = str(hostname)

    pre_hostname_change.send_robust(sender='config', old_hostname=old_hostname,
                                    new_hostname=hostname)

    LOGGER.info('Changing hostname to - %s', hostname)
    actions.superuser_run('hostname-change', [hostname])

    LOGGER.info('Setting domain name after hostname change - %s', domainname)
    actions.superuser_run('domainname-change', [domainname])

    post_hostname_change.send_robust(sender='config',
                                     old_hostname=old_hostname,
                                     new_hostname=hostname)


def set_domainname(domainname, old_domainname):
    """Sets machine domain name to domainname"""
    old_domainname = config.get_domainname()

    # Domain name should be ASCII. If it's unicode, convert to ASCII.
    domainname = str(domainname)

    LOGGER.info('Changing domain name to - %s', domainname)
    actions.superuser_run('domainname-change', [domainname])

    # Update domain registered with Name Services module.
    if old_domainname:
        domain_removed.send_robust(sender='config',
                                   domain_type='domain-type-static',
                                   name=old_domainname)

    if domainname:
        domain_added.send_robust(sender='config',
                                 domain_type='domain-type-static',
                                 name=domainname, services='__all__')
