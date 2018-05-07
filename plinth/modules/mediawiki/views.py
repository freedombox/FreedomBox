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
FreedomBox app for configuring MediaWiki.
"""

import logging

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import mediawiki

from . import get_public_registration_status
from .forms import MediaWikiForm

logger = logging.getLogger(__name__)


class MediaWikiServiceView(views.ServiceView):
    """Serve configuration page."""
    clients = mediawiki.clients
    description = mediawiki.description
    diagnostics_module_name = 'mediawiki'
    service_id = 'mediawiki'
    form_class = MediaWikiForm
    manual_page = mediawiki.manual_page
    show_status_block = False

    def get_initial(self):
        """Return the values to fill in the form."""
        initial = super().get_initial()
        initial.update({
            'enable_public_registrations': get_public_registration_status()
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

        if new_config['password']:
            actions.superuser_run('mediawiki', ['change-password'],
                                  input=new_config['password'].encode())
            messages.success(self.request, _('Password updated'))

        if app_same and pub_reg_same:
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_config['is_enabled']:
                self.service.enable()
                messages.success(self.request, _('Application enabled'))
            else:
                self.service.disable()
                messages.success(self.request, _('Application disabled'))

        if not pub_reg_same:
            # note action public-registration restarts, if running now
            if new_config['enable_public_registrations']:
                actions.superuser_run('mediawiki',
                                      ['public-registrations', 'enable'])
                messages.success(self.request,
                                 _('Public registrations enabled'))
            else:
                actions.superuser_run('mediawiki',
                                      ['public-registrations', 'disable'])
                messages.success(self.request,
                                 _('Public registrations disabled'))

        return super().form_valid(form)
