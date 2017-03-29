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
Plinth module to configure Tahoe-LAFS.
"""

import os

from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.utils import format_lazy
from plinth.modules import names


version = 1

depends = ['apps']

managed_services = ['tahoe-lafs']

managed_packages = ['tahoe-lafs']

title = _('Distributed File Storage (Tahoe-LAFS)')

description = [
    _('Tahoe-LAFS is a decentralized secure file storage system. It uses provider independent security to store files over a distributed network of storage nodes. Even if some of the nodes fail, your files can be retrieved from the remaining nodes.'),
    format_lazy(
        _('This {box_name} hosts a storage node and an introducer by default. Additional introducers can be added, which will introduce this node to the other storage nodes.'), box_name=_(cfg.box_name)),
    _('When enabled, the Tahoe-LAFS storage node\'s web interface will be available from <a href="/tahoe">/tahoe</a> '),
]

service = None

domain_name = None

domain_name_file = '/home/tahoe/domain_name'


def init():
    """Intialize the module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-hdd', 'tahoe:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)

        if is_enabled():
            add_shortcut()


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)

    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['http', 'https'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)


def post_setup(configured_domain_name):
    """
    Actions to be performed after installing tahoe-lafs package
    """
    domain_name = configured_domain_name
    actions.superuser_run('tahoe', ['setup', '--domain-name', domain_name])
    actions.superuser_run('tahoe', ['enable'])
    actions.run_as_user('tahoe', ['create-introducer'], become_user='tahoe')
    actions.run_as_user('tahoe', ['create-storage-node'], become_user='tahoe')


def get_domain_names():
    """Return the domain name(s)"""
    domain_names = []

    for domain_type, domains in names.domains.items():
        if domain_type == 'hiddenservice':
            continue
        for domain in domains:
            domain_names.append((domain, domain))

    return domain_names


def get_configured_domain_name():
    return domain_name


def is_setup():
    """Check whether Tahoe-LAFS is setup"""
    return os.path.exists(domain_name_file)


def add_shortcut():
    """Helper method to add a shortcut to the front page."""
    frontpage.add_shortcut(
        'tahoe', title, url='/tahoe', login_required=True)


def is_running():
    """Return whether the service is running."""
    # TODO check whether the nodes are running
    return action_utils.service_is_running(managed_services[0])


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled(managed_services[0]) and
            action_utils.webserver_is_enabled('tahoe-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('tahoe', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('tahoe', ['disable'])
    frontpage.remove_shortcut('tahoe')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all(
            'https://{host}/tahoe', check_certificate=False))

    return results
