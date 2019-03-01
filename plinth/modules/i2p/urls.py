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
URLs for the I2P module.
"""

from django.conf.urls import url

from plinth.modules.i2p import views

urlpatterns = [
    url(r'^apps/i2p/$', views.I2PServiceView.as_view(), name='index'),
    url(r'^apps/i2p/frame/tunnels/?$', views.create_i2p_frame_view(
        "I2P Proxies and Tunnels", "i2ptunnel"
    ), name='frame_tunnels'),
    url(r'^apps/i2p/frame/torrent/?$', views.create_i2p_frame_view(
        "Anonymous torrents", "i2psnark"
    ), name='frame_torrent'),

]
