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

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        form_data = form.cleaned_data

        if form_data['password']:
            actions.superuser_run('mediawiki', ['change-password'],
                                  input=form_data['password'].encode())
            messages.success(self.request, _('Password updated'))

        return super().form_valid(form)
