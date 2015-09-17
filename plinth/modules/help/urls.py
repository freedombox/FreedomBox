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
URLs for the Help module
"""

from django.conf.urls import patterns, url


urlpatterns = patterns(  # pylint: disable-msg=C0103
    'plinth.modules.help.help',
    # having two urls for one page is a hack to help the current url/menu
    # system highlight the correct menu item. Every submenu-item with the same
    # url prefix as the main-menu is highlighted automatically.
    url(r'^help/$', 'index', name='index'),
    url(r'^help/index/$', 'index', name='index_explicit'),
    url(r'^help/about/$', 'about', name='about'),
    url(r'^help/manual/$', 'manual', name='manual'),
)
