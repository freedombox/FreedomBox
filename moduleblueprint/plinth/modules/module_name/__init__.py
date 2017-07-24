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
Plinth module for {{module_name}}.
"""
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import action_utils
from plinth import cfg
from plinth import frontpage
from plinth import service as service_module
from plinth.utils import format_lazy
from plinth.views import ServiceView


version = 1

depends = ['apps']

title = _('{{module_title}}')

service = None
description = [
    "{{module_description}}"
]

def init():
    """Initialize the {{module_name}} module."""
    menu = cfg.main_menu.get('apps:index')
    menu.add_urlname(title, 'glyphicon-retweet', '{{module_name}}:index')

    global service
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        service = service_module.Service(
            managed_services[0], title, ports=['{{module_name}}-plinth'],
            is_external=True, enable=enable, disable=disable)

        if service.is_enabled():
            add_shortcut()

class {{module_name}}ServiceView(ServiceView):
    service_id = managed_services[0]
    diagnostics_{{module_name}} = "{{module_name}}"
	description = description

def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    global service
    if service is None:
        service = service_module.Service(
            managed_services[0], title, ports=['{{module_name}}-plinth'],
            is_external=True, enable=enable, disable=disable)
    helper.call('post', service.notify_enabled, None, True)
    helper.call('post', add_shortcut)

def add_shortcut():
    frontpage.add_shortcut('{{module_name}}', title,
                           details=description,
                           configure_url=reverse_lazy('{{module_name}}:index'),
                           login_required=True)

def enable():
    """Enable the module."""
    actions.superuser_run('service', ['enable', managed_services[0]])
    add_shortcut()

def disable():
    """Disable the module."""
    actions.superuser_run('service', ['disable', managed_services[0]])
    frontpage.remove_shortcut('{{module_name}}')


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    
return results

def is_enabled():
    """Return whether the module is enabled."""
    return action_utils.webserver_is_enabled('{{module_name}}')