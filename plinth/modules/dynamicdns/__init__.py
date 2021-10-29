# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure ez-ipupdate client.
"""

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import cfg, menu
from plinth.modules.backups.components import BackupRestore
from plinth.modules.names.components import DomainType
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages
from plinth.signals import domain_added
from plinth.utils import format_lazy

from . import manifest

version = 1

is_essential = True

depends = ['names']

managed_packages = ['ez-ipupdate']

_description = [
    format_lazy(
        _('If your Internet provider changes your IP address periodically '
          '(i.e. every 24h), it may be hard for others to find you on the '
          'Internet. This will prevent others from finding services which are '
          'provided by this {box_name}.'), box_name=_(cfg.box_name)),
    _('The solution is to assign a DNS name to your IP address and '
      'update the DNS name every time your IP is changed by your '
      'Internet provider. Dynamic DNS allows you to push your current '
      'public IP address to a '
      '<a href=\'http://gnudip2.sourceforge.net/\' target=\'_blank\'> '
      'GnuDIP</a> server. Afterwards, the server will assign your DNS name '
      'to the new IP, and if someone from the Internet asks for your DNS '
      'name, they will get a response with your current IP address.')
]

app = None


class DynamicDNSApp(app_module.App):
    """FreedomBox app for Dynamic DNS."""

    app_id = 'dynamicdns'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=version,
                               is_essential=is_essential, depends=depends,
                               name=_('Dynamic DNS Client'), icon='fa-refresh',
                               description=_description,
                               manual_page='DynamicDNS')
        self.add(info)

        menu_item = menu.Menu('menu-dynamicdns', info.name, None, info.icon,
                              'dynamicdns:index', parent_url_name='system')
        self.add(menu_item)

        packages = Packages('packages-dynamicdns', managed_packages)
        self.add(packages)

        domain_type = DomainType('domain-type-dynamic',
                                 _('Dynamic Domain Name'), 'dynamicdns:index',
                                 can_have_certificate=True)
        self.add(domain_type)

        users_and_groups = UsersAndGroups('users-and-groups-dynamicdns',
                                          reserved_usernames=['ez-ipupd'])
        self.add(users_and_groups)

        backup_restore = BackupRestore('backup-restore-dynamicdns',
                                       **manifest.backup)
        self.add(backup_restore)

        current_status = get_status()
        if current_status['enabled']:
            domain_added.send_robust(sender='dynamicdns',
                                     domain_type='domain-type-dynamic',
                                     name=current_status['dynamicdns_domain'],
                                     services='__all__')

    def is_enabled(self):
        """Return whether all the leader components are enabled.

        Return True when there are no leader components and DynamicDNS setup
        is done.
        """
        return super().is_enabled() and get_status()['enabled']


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)


def get_status():
    """Return the current status."""
    # TODO: use key/value instead of hard coded value list
    status = {}
    output = actions.superuser_run('dynamicdns', ['status'])
    details = output.split()
    status['enabled'] = (output.split()[0] == 'enabled')

    if len(details) > 1:
        if details[1] == 'disabled':
            status['dynamicdns_server'] = ''
        else:
            status['dynamicdns_server'] = details[1].replace("'", "")
    else:
        status['dynamicdns_server'] = ''

    if len(details) > 2:
        if details[2] == 'disabled':
            status['dynamicdns_domain'] = ''
        else:
            status['dynamicdns_domain'] = details[2].replace("'", "")
    else:
        status['dynamicdns_domain'] = ''

    if len(details) > 3:
        if details[3] == 'disabled':
            status['dynamicdns_user'] = ''
        else:
            status['dynamicdns_user'] = details[3].replace("'", "")
    else:
        status['dynamicdns_user'] = ''

    if len(details) > 4:
        if details[4] == 'disabled':
            status['dynamicdns_secret'] = ''
        else:
            status['dynamicdns_secret'] = details[4].replace("'", "")
    else:
        status['dynamicdns_secret'] = ''

    if len(details) > 5:
        if details[5] == 'disabled':
            status['dynamicdns_ipurl'] = ''
        else:
            status['dynamicdns_ipurl'] = details[5].replace("'", "")
    else:
        status['dynamicdns_ipurl'] = ''

    if len(details) > 6:
        if details[6] == 'disabled':
            status['dynamicdns_update_url'] = ''
        else:
            status['dynamicdns_update_url'] = details[6].replace("'", "")
    else:
        status['dynamicdns_update_url'] = ''

    if len(details) > 7:
        status['disable_SSL_cert_check'] = (output.split()[7] == 'enabled')
    else:
        status['disable_SSL_cert_check'] = False

    if len(details) > 8:
        status['use_http_basic_auth'] = (output.split()[8] == 'enabled')
    else:
        status['use_http_basic_auth'] = False

    if len(details) > 9:
        status['use_ipv6'] = (output.split()[9] == 'enabled')
    else:
        status['use_ipv6'] = False

    if not status['dynamicdns_server'] and not status['dynamicdns_update_url']:
        status['service_type'] = 'GnuDIP'
    elif not status['dynamicdns_server'] and status['dynamicdns_update_url']:
        status['service_type'] = 'other'
    else:
        status['service_type'] = 'GnuDIP'

    return status
