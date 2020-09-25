# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Cockpit.
"""

from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, frontpage, menu
from plinth.daemon import Daemon
from plinth.modules import names
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.signals import domain_added, domain_removed
from plinth.utils import format_lazy

from . import utils
from .manifest import backup, clients  # noqa, pylint: disable=unused-import

version = 1

is_essential = True

managed_services = ['cockpit.socket']

managed_packages = ['cockpit']

_description = [
    format_lazy(
        _('Cockpit is a server manager that makes it easy to administer '
          'GNU/Linux servers via a web browser. On a {box_name}, controls '
          'are available for many advanced functions that are not usually '
          'required. A web based terminal for console operations is also '
          'available.'), box_name=_(cfg.box_name)),
    format_lazy(
        _('Cockpit can be used to perform advanced storage operations such as '
          'disk partitioning and RAID management. It can also be used for '
          'opening custom firewall ports and advanced networking such as '
          'bonding, bridging and VLAN management.')),
    format_lazy(
        _('It can be accessed by <a href="{users_url}">any user</a> on '
          '{box_name} belonging to the admin group.'),
        box_name=_(cfg.box_name), users_url=reverse_lazy('users:index')),
    format_lazy(
        _('Cockpit requires that you access it through a domain name. '
          'It will not work when accessed using an IP address as part'
          ' of the URL.')),
]

app = None


class CockpitApp(app_module.App):
    """FreedomBox app for Cockpit."""

    app_id = 'cockpit'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, name=_('Cockpit'),
                               icon='fa-wrench', icon_filename='cockpit',
                               short_description=_('Server Administration'),
                               description=_description, manual_page='Cockpit',
                               clients=clients)
        self.add(info)

        menu_item = menu.Menu('menu-cockpit', info.name,
                              info.short_description, info.icon,
                              'cockpit:index', parent_url_name='system')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-cockpit', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename,
                                      url='/_cockpit/', clients=info.clients,
                                      login_required=True,
                                      allowed_groups=['admin'])
        self.add(shortcut)

        firewall = Firewall('firewall-cockpit', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-cockpit', 'cockpit-freedombox',
                              urls=['https://{host}/_cockpit/'])
        self.add(webserver)

        daemon = Daemon('daemon-cockpit', managed_services[0])
        self.add(daemon)

        domain_added.connect(on_domain_added)
        domain_removed.connect(on_domain_removed)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    domains = names.components.DomainName.list_names('https')
    helper.call('post', actions.superuser_run, 'cockpit',
                ['setup'] + list(domains))
    helper.call('post', app.enable)


def on_domain_added(sender, domain_type, name, description='', services=None,
                    **kwargs):
    """Handle addition of a new domain."""
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        if name not in utils.get_domains():
            actions.superuser_run('cockpit', ['add-domain', name])
            actions.superuser_run('service',
                                  ['try-restart', managed_services[0]])


def on_domain_removed(sender, domain_type, name, **kwargs):
    """Handle removal of a domain."""
    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        if name in utils.get_domains():
            actions.superuser_run('cockpit', ['remove-domain', name])
            actions.superuser_run('service',
                                  ['try-restart', managed_services[0]])
