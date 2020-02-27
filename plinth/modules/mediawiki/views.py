# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for configuring MediaWiki.
"""

import logging

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import mediawiki

from . import (get_default_skin, is_private_mode_enabled,
               is_public_registration_enabled)
from .forms import MediaWikiForm

logger = logging.getLogger(__name__)


class MediaWikiAppView(views.AppView):
    """App configuration page."""
    app_id = 'mediawiki'
    form_class = MediaWikiForm
    show_status_block = False
    template_name = 'mediawiki.html'

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'enable_public_registrations': is_public_registration_enabled(),
            'enable_private_mode': is_private_mode_enabled(),
            'default_skin': get_default_skin()
        })
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data

        def is_unchanged(key):
            return old_config[key] == new_config[key]

        app_same = is_unchanged('is_enabled')
        pub_reg_same = is_unchanged('enable_public_registrations')
        private_mode_same = is_unchanged('enable_private_mode')
        default_skin_same = is_unchanged('default_skin')

        if new_config['password']:
            actions.superuser_run('mediawiki', ['change-password'],
                                  input=new_config['password'].encode())
            messages.success(self.request, _('Password updated'))

        if (app_same and pub_reg_same and private_mode_same
                and default_skin_same):
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_config['is_enabled']:
                self.app.enable()
            else:
                self.app.disable()

        if not pub_reg_same:
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

        if not private_mode_same:
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

        if not default_skin_same:
            actions.superuser_run(
                'mediawiki', ['set-default-skin', new_config['default_skin']])
            messages.success(self.request, _('Default skin changed'))

        return super().form_valid(form)
