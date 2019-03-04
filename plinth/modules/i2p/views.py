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
from django.template.response import TemplateResponse
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.utils.translation import ugettext_lazy

import plinth.modules.i2p as i2p
from plinth.views import ServiceView

subsubmenu = [{
    'url': reverse_lazy('i2p:index'),
    'text': ugettext_lazy('Configure')
}, {
    'url': reverse_lazy('i2p:frame_tunnels'),
    'text': ugettext_lazy('Proxies')
}, {
    'url': reverse_lazy('i2p:frame_torrent'),
    'text': ugettext_lazy('Anonymous torrents')
}]


class I2PServiceView(ServiceView):
    """Serve configuration page."""
    service_id = i2p.servicename
    description = i2p.description
    diagnostics_module_name = i2p.servicename
    show_status_block = False

    def get_context_data(self, **kwargs):
        """Return the context data for rendering the template view."""
        context = super().get_context_data(**kwargs)
        context['subsubmenu'] = subsubmenu
        context['clients'] = i2p.clients
        return context


def _create_i2p_frame_view(title, rel_path, description):
    """
    Creates a view with an iframe to the given path

    This is primarily used as a shortcut to pages under /i2p/

    :param title: the page title that will have to be i18n
    :type title: basestring
    :param rel_path: the URL path after /i2p/<rel_path>
    :type rel_path: basestring
    :return: a django view
    :rtype: callable
    """
    path = "/i2p/" + rel_path

    def i2p_frame_view(request):
        return TemplateResponse(
            request, 'i2p_frame.html', {
                'title': _(title),
                'subsubmenu': subsubmenu,
                'path': path,
                'description': description
            })

    return i2p_frame_view


i2p_frame_tunnels = _create_i2p_frame_view(
    "I2P Proxies and Tunnels", "i2ptunnel", [
        _('I2P has the concept of tunnels. These enter an exit the network and are configured and (de)activated here.'),
        _('HTTP/S SOCKS5 proxies are entry tunnels, so they are configured here.'),
        _('In order to allow usage by other members of your network, '
          'select the proxy then the interface you want your proxies to be bound to and save the settings.'
          'The interface is in the "Reachable by" dropdown list.'),
        _('You can find the IP addresses of your interfaces/connections <a href="/plinth/sys/networks/">here</a>'),
    ]
)
i2p_frame_torrent = _create_i2p_frame_view(
    "Anonymous torrents", "i2psnark", [
        _('Track the progress of your anonymous torrent downloads here.'),
        _('You can find a list of trackers on the '
          '<a href="/i2p/i2psnark/configure" target="i2p-frame" >Configuration page</a>'),
    ]
)
