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
Plinth module to configure Privoxy.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy
from plinth.views import ServiceView


version = 1

is_essential = False

managed_services = ['privoxy']

managed_packages = ['privoxy']

title = _('Web Proxy \n (Privoxy)')

description = [
    _('Privoxy is a non-caching web proxy with advanced filtering '
      'capabilities for enhancing privacy, modifying web page data and '
      'HTTP headers, controlling access, and removing ads and other '
      'obnoxious Internet junk. '),

    format_lazy(
        _('You can use Privoxy by modifying your browser proxy settings to '
          'your {box_name} hostname (or IP address) with port 8118. '
          'While using Privoxy, you can see its configuration details and '
          'documentation at '
          '<a href="http://config.privoxy.org">http://config.privoxy.org/</a> '
          'or <a href="http://p.p">http://p.p</a>.'),
        box_name=_(cfg.box_name)),
]

reserved_usernames = ['privoxy']

service = None


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-cloud-upload', 'privoxy:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['privoxy'],
            is_external=False,
            enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'privoxy', ['pre-install'])
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['privoxy'],
            is_external=False,
            enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def add_shortcut():
    frontpage.add_shortcut('privoxy', title,
                           details=description,
                           configure_url=reverse_lazy('privoxy:index'),
                           login_required=True)


def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()


def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('privoxy')


class PrivoxyServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_module_name = 'privoxy'
    description = description


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.append(action_utils.diagnose_port_listening(8118, 'tcp4'))
    results.append(action_utils.diagnose_port_listening(8118, 'tcp6'))
    results.append(action_utils.diagnose_url('https://www.debian.org'))
    results.extend(diagnose_url_with_proxy())

    return results


def diagnose_url_with_proxy():
    """Run a diagnostic on a URL with a proxy."""
    url = 'https://debian.org/'  # Gives a simple redirect to www.

    results = []
    for address in action_utils.get_addresses():
        proxy = 'http://{host}:8118/'.format(host=address['url_address'])
        env = {'https_proxy': proxy}

        result = action_utils.diagnose_url(url, kind=address['kind'], env=env)
        result[0] = _('Access {url} with proxy {proxy} on tcp{kind}') \
            .format(url=url, proxy=proxy, kind=address['kind'])
        results.append(result)

    return results
