# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox views for basic system configuration."""

import logging

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import views
from plinth.modules import config
from plinth.signals import (domain_added, domain_removed, post_hostname_change,
                            pre_hostname_change)

from . import privileged
from .forms import ConfigurationForm

LOGGER = logging.getLogger(__name__)


class ConfigAppView(views.AppView):
    """Serve configuration page."""

    form_class = ConfigurationForm
    app_id = 'config'

    def get_initial(self):
        """Return the current status."""
        return {
            'hostname': config.get_hostname(),
            'domainname': config.get_domainname(),
            'homepage': config.get_home_page(),
            'advanced_mode': config.get_advanced_mode(),
            'logging_mode': privileged.get_logging_mode(),
        }

    def form_valid(self, form):
        """Apply the form changes."""
        old_status = form.initial
        new_status = form.cleaned_data

        is_changed = False

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

        if old_status['logging_mode'] != new_status['logging_mode']:
            privileged.set_logging_mode(new_status['logging_mode'])
            is_changed = True

        if is_changed:
            messages.success(self.request, _('Configuration updated'))

        return super().form_valid(form)


def set_hostname(hostname):
    """Set machine hostname and send signals before and after."""
    old_hostname = config.get_hostname()
    domainname = config.get_domainname()

    # Hostname should be ASCII. If it's unicode but passed our
    # valid_hostname check, convert
    hostname = str(hostname)

    pre_hostname_change.send_robust(sender='config', old_hostname=old_hostname,
                                    new_hostname=hostname)

    LOGGER.info('Changing hostname to - %s', hostname)
    privileged.set_hostname(hostname)

    LOGGER.info('Setting domain name after hostname change - %s', domainname)
    privileged.set_domainname(domainname)

    post_hostname_change.send_robust(sender='config',
                                     old_hostname=old_hostname,
                                     new_hostname=hostname)


def set_domainname(domainname, old_domainname):
    """Set machine domain name to domainname."""
    old_domainname = config.get_domainname()

    # Domain name is not case sensitive, but Let's Encrypt certificate
    # paths use lower-case domain name.
    domainname = domainname.lower()

    LOGGER.info('Changing domain name to - %s', domainname)
    privileged.set_domainname(domainname)

    # Update domain registered with Name Services module.
    if old_domainname:
        domain_removed.send_robust(sender='config',
                                   domain_type='domain-type-static',
                                   name=old_domainname)

    if domainname:
        domain_added.send_robust(sender='config',
                                 domain_type='domain-type-static',
                                 name=domainname, services='__all__')
