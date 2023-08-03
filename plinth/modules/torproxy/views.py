# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring Tor Proxy."""

import logging

from django.utils.translation import gettext_noop
from django.views.generic.edit import FormView

from plinth import app as app_module
from plinth import operation as operation_module
from plinth.views import AppView

from . import privileged
from . import utils as tor_utils
from .forms import TorProxyForm

logger = logging.getLogger(__name__)


class TorProxyAppView(AppView):
    """Show Tor Proxy app main page."""

    app_id = 'torproxy'
    template_name = 'torproxy.html'
    form_class = TorProxyForm
    prefix = 'torproxy'

    status = None

    def get_initial(self):
        """Return the values to fill in the form."""
        if not self.status:
            self.status = tor_utils.get_status()

        initial = super().get_initial()
        initial.update(self.status)
        return initial

    def get_context_data(self, *args, **kwargs):
        """Add additional context data for template."""
        if not self.status:
            self.status = tor_utils.get_status()

        context = super().get_context_data(*args, **kwargs)
        context['status'] = self.status
        return context

    def form_valid(self, form):
        """Configure tor app on successful form submission."""
        operation_module.manager.new(self.app_id,
                                     gettext_noop('Updating configuration'),
                                     _apply_changes,
                                     [form.initial, form.cleaned_data],
                                     show_notification=False)
        # Skip check for 'Settings unchanged' message by calling grandparent
        return super(FormView, self).form_valid(form)


def _apply_changes(old_status, new_status):
    """Try to apply changes and handle errors."""
    logger.info('torproxy: applying configuration changes')
    exception_to_update = None
    message = None
    try:
        __apply_changes(old_status, new_status)
    except Exception as exception:
        exception_to_update = exception
        message = gettext_noop('Error configuring app: {error}').format(
            error=exception)
    else:
        message = gettext_noop('Configuration updated.')

    logger.info('torproxy: configuration changes completed')
    operation = operation_module.Operation.get_operation()
    operation.on_update(message, exception_to_update)


def __apply_changes(old_status, new_status):
    """Apply the changes."""
    needs_restart = False
    arguments = {}

    app = app_module.App.get('torproxy')
    is_enabled = app.is_enabled()

    if old_status['apt_transport_tor_enabled'] != \
       new_status['apt_transport_tor_enabled']:
        arguments['apt_transport_tor'] = (
            is_enabled and new_status['apt_transport_tor_enabled'])

    if old_status['use_upstream_bridges'] != \
       new_status['use_upstream_bridges']:
        arguments['use_upstream_bridges'] = new_status['use_upstream_bridges']
        needs_restart = True

    if old_status['upstream_bridges'] != new_status['upstream_bridges']:
        arguments['upstream_bridges'] = new_status['upstream_bridges']
        needs_restart = True

    if arguments:
        privileged.configure(**arguments)

    if needs_restart and is_enabled:
        privileged.restart()
