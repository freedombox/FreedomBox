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
URLs for the PageKite module
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required

from .views import DefaultServiceView, CustomServiceView, ConfigurationView, \
    DeleteServiceView, index


urlpatterns = patterns(  # pylint: disable-msg=C0103
    'plinth.modules.pagekite.views',
    url(r'^apps/pagekite/$', login_required(index), name='index'),
    url(r'^apps/pagekite/configure/$',
        login_required(ConfigurationView.as_view()), name='configure'),
    url(r'^apps/pagekite/services/default$',
        login_required(DefaultServiceView.as_view()), name='default-services'),
    url(r'^apps/pagekite/services/custom$',
        login_required(CustomServiceView.as_view()), name='custom-services'),
    url(r'^apps/pagekite/services/custom/delete$',
        login_required(DeleteServiceView.as_view()), name='delete-custom-service'),
    )
