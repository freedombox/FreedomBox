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
Main Plinth views
"""

from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect
from plinth.modules.dashboard import views as dashboard_views


def index(request):
    """Serve the main index page"""
    if request.user.is_authenticated():
        return dashboard_views.Index.as_view()(request)

    return HttpResponseRedirect(reverse('help:about'))
