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

import json
import os

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils
from plinth import actions
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.menu import main_menu
from plinth.utils import format_lazy

from .errors import TahoeConfigurationError

version = 1

managed_services = ['tahoe-lafs']

managed_packages = ['tahoe-lafs']

title = _('Distributed File Storage (Tahoe-LAFS)')

service = None

tahoe_home = '/var/lib/tahoe-lafs'
introducer_name = 'introducer'
storage_node_name = 'storage_node'
domain_name_file = os.path.join(tahoe_home, 'domain_name')
introducers_file = os.path.join(
    tahoe_home, '{}/private/introducers.yaml'.format(storage_node_name))
introducer_furl_file = os.path.join(
    tahoe_home, '{0}/private/{0}.furl'.format(introducer_name))


def is_setup():
    """Check whether Tahoe-LAFS is setup"""
    return os.path.exists(domain_name_file)


def get_configured_domain_name():
    """Extract and return the domain name from the domain name file.
    Throws TahoeConfigurationError if the domain name file is not found.
    """
    if not os.path.exists(domain_name_file):
        raise TahoeConfigurationError
    else:
        with open(domain_name_file) as dnf:
            return dnf.read().rstrip()


description = [
    _('Tahoe-LAFS is a decentralized secure file storage system. '
      'It uses provider independent security to store files over a '
      'distributed network of storage nodes. Even if some of the nodes fail, '
      'your files can be retrieved from the remaining nodes.'),
    format_lazy(
        _('This {box_name} hosts a storage node and an introducer by default. '
          'Additional introducers can be added, which will introduce this '
          'node to the other storage nodes.'),
        box_name=_(cfg.box_name)),
]


def init():
    """Intialize the module."""
    menu = main_menu.get('apps')
    menu.add_urlname(title, 'glyphicon-hdd', 'tahoe:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup' and is_setup():
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['tahoe-plinth'],
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


def post_setup(configured_domain_name):
    """Actions to be performed after installing tahoe-lafs package."""
    actions.superuser_run('tahoe-lafs',
                          ['setup', '--domain-name', configured_domain_name])
    actions.superuser_run('tahoe-lafs', ['enable'])
    actions.run_as_user('tahoe-lafs', ['create-introducer'],
                        become_user='tahoe-lafs')
    actions.run_as_user('tahoe-lafs', ['create-storage-node'],
                        become_user='tahoe-lafs')
    actions.superuser_run('tahoe-lafs', ['autostart'])

    global service
    if service is None:
        service = service_module.Service(
            managed_services[0],
            title,
            ports=['tahoe-plinth'],
            is_external=True,
            is_enabled=is_enabled,
            enable=enable,
            disable=disable,
            is_running=is_running)
    service.notify_enabled(None, True)
    add_shortcut()


def add_shortcut():
    """Helper method to add a shortcut to the front page."""
    # BUG: Current logo appears squashed on front page.
    frontpage.add_shortcut(
        'tahoe-lafs', title,
        url='https://{}:5678'.format(get_configured_domain_name()),
        login_required=True)


def is_running():
    """Return whether the service is running."""
    return action_utils.service_is_running(managed_services[0])


def is_enabled():
    """Return whether the module is enabled."""
    return (action_utils.service_is_enabled(managed_services[0]) and
            action_utils.webserver_is_enabled('tahoe-plinth'))


def enable():
    """Enable the module."""
    actions.superuser_run('tahoe-lafs', ['enable'])
    add_shortcut()


def disable():
    """Enable the module."""
    actions.superuser_run('tahoe-lafs', ['disable'])
    frontpage.remove_shortcut('tahoe-lafs')


def diagnose():
    """Run diagnostics and return the results."""
    return [action_utils.diagnose_url(
        'http://localhost:5678', kind='4', check_certificate=False),
            action_utils.diagnose_url(
                'http://localhost:5678', kind='6', check_certificate=False),
            action_utils.diagnose_url(
                'http://{}:5678'.format(get_configured_domain_name()),
                kind='4',
                check_certificate=False)]


def add_introducer(introducer):
    """Add an introducer to the storage node's list of introducers.
    Param introducer must be a tuple of (pet_name, furl)
    """
    actions.run_as_user('tahoe-lafs',
                        ['add-introducer',
                         "--introducer",
                         ",".join(introducer)],
                        become_user='tahoe-lafs')


def remove_introducer(pet_name):
    """Rename the introducer entry in the introducers.yaml file specified by
    the param pet_name.
    """
    actions.run_as_user('tahoe-lafs',
                        ['remove-introducer', '--pet-name', pet_name],
                        become_user='tahoe-lafs')


def get_introducers():
    """Return a dictionary of all introducers and their furls added to the
    storage node running on this FreedomBox.
    """
    introducers = actions.run_as_user('tahoe-lafs', ['get-introducers'],
                                      become_user='tahoe-lafs')

    return json.loads(introducers)


def get_local_introducer():
    """Return the name and furl of the introducer created on this FreedomBox.
    """
    introducer = actions.run_as_user('tahoe-lafs', ['get-local-introducer'],
                                     become_user='tahoe-lafs')

    return json.loads(introducer)
