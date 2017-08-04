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
Plinth module for configuring Transmission Server
"""

import logging

from django.contrib import messages
from django.utils.translation import ugettext as _

from plinth import actions, views
from plinth.modules import mediawiki

from .forms import MediawikiForm

logger = logging.getLogger(__name__)


class MediawikiServiceView(views.ServiceView):
    """Serve configuration page."""
    clients = mediawiki.clients
    description = mediawiki.description
    diagnostics_module_name = 'mediawiki'
    form_class = MediawikiForm
    service_id = mediawiki.managed_services[0]

    def form_valid(self, form):
        """Apply the changes submitted in the form."""
        form_data = form.cleaned_data

        actions.superuser_run(
            'mediawiki',
            ['change-password', '--password', form_data['password']])
        messages.success(self.request, _('Password Updated'))

        return super().form_valid(form)
