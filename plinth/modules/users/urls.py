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
URLs for the Users module
"""

from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy

from . import views


urlpatterns = patterns(
    '',
    url(r'^sys/users/$', login_required(views.UserList.as_view()),
        name='index'),
    url(r'^sys/users/create/$', login_required(views.UserCreate.as_view()),
        name='create'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/edit/$',
        login_required(views.UserUpdate.as_view()), name='edit'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/delete/$',
        login_required(views.UserDelete.as_view()), name='delete'),
    url(r'^sys/users/(?P<slug>[\w.@+-]+)/change_password/$',
        login_required(views.UserChangePassword.as_view()),
        name='change_password'),
    # Add Django's login/logout urls
    url(r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'template_name': 'login.html'}, name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': reverse_lazy('index')}, name='logout'),
)
