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

from .forms import MediaWikiForm
from . import get_public_registration_status

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
            'enable_public_registration': get_public_registration_status()
        })
        return initial

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        old_config = self.get_initial()
        new_config = form.cleaned_data
        app_same = old_config['is_enabled'] == new_config['is_enabled']
        pubreg_same = old_config['enable_public_registration'] == \
                      new_config['enable_public_registration']
        if new_config['password']:
            actions.superuser_run('mediawiki', ['change-password'],
                                  input=new_config['password'].encode())
            messages.success(self.request, _('Password updated'))
        if app_same and pubreg_same:
            if not self.request._messages._queued_messages:
                messages.info(self.request, _('Setting unchanged'))
        elif not app_same:
            if new_config['is_enabled']:
                self.service.enable()
                messages.success(self.request, _('Application enabled'))
            else:
                self.service.disable()
                messages.success(self.request, _('Application disabled'))

        if not pubreg_same:
            # note action public-registration restarts, if running now
            if new_config['enable_public_registration']:
                actions.superuser_run('mediawiki',
                                      ['public-registration', 'true'])
                messages.success(self.request,
                                 _('Public registration enabled'))
            else:
                actions.superuser_run('mediawiki',
                                      ['public-registration', 'false'])
                messages.success(self.request,
                                 _('Public registration disabled'))

        return super().form_valid(form)
