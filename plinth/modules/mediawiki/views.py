# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring MediaWiki.
"""

import logging

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import actions, views
from plinth.errors import ActionError
from plinth.modules import mediawiki

from . import (get_default_skin, get_server_url, is_private_mode_enabled,
               is_public_registration_enabled)
from .forms import MediaWikiForm

logger = logging.getLogger(__name__)


class MediaWikiAppView(views.AppView):
    """App configuration page."""
    app_id = 'mediawiki'
    form_class = MediaWikiForm
    template_name = 'mediawiki.html'

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'enable_public_registrations': is_public_registration_enabled(),
            'enable_private_mode': is_private_mode_enabled(),
            'default_skin': get_default_skin(),
            'domain': get_server_url()
        })
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        def is_changed(key):
            return old_config.get(key) != new_config.get(key)

        if new_config['password']:
            try:
                actions.superuser_run('mediawiki', ['change-password'],
                                      input=new_config['password'].encode())
                messages.success(self.request, _('Password updated'))
            except ActionError as exception:
                logger.exception('Failed to update password: %s', exception)
                messages.error(
                    self.request,
                    _('Password update failed. Please choose a stronger '
                      'password'))

        if is_changed('enable_public_registrations'):
            # note action public-registration restarts, if running now
            if new_config['enable_public_registrations']:
                if not new_config['enable_private_mode']:
                    actions.superuser_run('mediawiki',
                                          ['public-registrations', 'enable'])
                    messages.success(self.request,
                                     _('Public registrations enabled'))
                else:
                    messages.warning(
                        self.request, 'Public registrations ' +
                        'cannot be enabled when private mode is enabled')
            else:
                actions.superuser_run('mediawiki',
                                      ['public-registrations', 'disable'])
                messages.success(self.request,
                                 _('Public registrations disabled'))

        if is_changed('enable_private_mode'):
            if new_config['enable_private_mode']:
                actions.superuser_run('mediawiki', ['private-mode', 'enable'])
                messages.success(self.request, _('Private mode enabled'))
                if new_config['enable_public_registrations']:
                    # If public registrations are enabled, then disable it
                    actions.superuser_run('mediawiki',
                                          ['public-registrations', 'disable'])
            else:
                actions.superuser_run('mediawiki', ['private-mode', 'disable'])
                messages.success(self.request, _('Private mode disabled'))

            shortcut = mediawiki.app.get_component('shortcut-mediawiki')
            shortcut.login_required = new_config['enable_private_mode']

        if is_changed('default_skin'):
            mediawiki.set_default_skin(new_config['default_skin'])
            messages.success(self.request, _('Default skin changed'))

        if is_changed('domain'):
            mediawiki.set_server_url(new_config['domain'])
            messages.success(self.request, _('Domain name updated'))

        return super().form_valid(form)
