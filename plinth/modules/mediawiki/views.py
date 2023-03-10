# SPDX-License-Identifier: AGPL-3.0-or-later
"""FreedomBox app for configuring MediaWiki."""

import logging

from django.contrib import messages
from django.utils.translation import gettext as _

from plinth import app as app_module
from plinth import views
from plinth.modules import mediawiki

from . import (get_default_skin,
               get_server_url, get_site_name, get_default_language, privileged)
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
            'enable_public_registrations':
                privileged.public_registrations('status'),
            'enable_private_mode':
                privileged.private_mode('status'),
            'default_skin':
                get_default_skin(),
            'domain':
                get_server_url(),
            'site_name':
                get_site_name(),
            'default_lang':
                get_default_language()
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
                privileged.change_password('admin', new_config['password'])
                messages.success(self.request, _('Password updated'))
            except Exception as exception:
                logger.exception('Failed to update password: %s', exception)
                messages.error(
                    self.request,
                    _('Password update failed. Please choose a stronger '
                      'password'))

        if is_changed('enable_public_registrations'):
            # note action public-registration restarts, if running now
            if new_config['enable_public_registrations']:
                if not new_config['enable_private_mode']:
                    privileged.public_registrations('enable')
                    messages.success(self.request,
                                     _('Public registrations enabled'))
                else:
                    messages.warning(
                        self.request, 'Public registrations ' +
                        'cannot be enabled when private mode is enabled')
            else:
                privileged.public_registrations('disable')
                messages.success(self.request,
                                 _('Public registrations disabled'))

        if is_changed('enable_private_mode'):
            if new_config['enable_private_mode']:
                privileged.private_mode('enable')
                messages.success(self.request, _('Private mode enabled'))
                if new_config['enable_public_registrations']:
                    # If public registrations are enabled, then disable it
                    privileged.public_registrations('disable')
            else:
                privileged.private_mode('disable')
                messages.success(self.request, _('Private mode disabled'))

            app = app_module.App.get('mediawiki')
            shortcut = app.get_component('shortcut-mediawiki')
            shortcut.login_required = new_config['enable_private_mode']

        if is_changed('default_skin'):
            privileged.set_default_skin(new_config['default_skin'])
            messages.success(self.request, _('Default skin changed'))

        if is_changed('domain'):
            mediawiki.set_server_url(new_config['domain'])
            messages.success(self.request, _('Domain name updated'))

        if is_changed('site_name'):
            privileged.set_site_name(new_config['site_name'])
            messages.success(self.request, _('Site name updated'))

        if is_changed('default_lang'):
            privileged.set_default_language(new_config['default_lang'])
            messages.success(self.request, _('Default language changed'))

        return super().form_valid(form)
