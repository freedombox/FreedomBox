# SPDX-License-Identifier: AGPL-3.0-or-later

import os

import augeas
from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.daemon import Daemon
from plinth.errors import DomainNotRegisteredError
from plinth.modules.apache.components import Webserver, diagnose_url
from plinth.modules.firewall.components import Firewall
from plinth.package import Packages
from plinth.utils import format_lazy

domain_name_file = "/etc/diaspora/domain_name"
lazy_domain_name = None  # To avoid repeatedly reading from file


def is_setup():
    return os.path.exists(domain_name_file)


def get_configured_domain_name():
    global lazy_domain_name
    if lazy_domain_name:
        return lazy_domain_name

    if not is_setup():
        raise DomainNotRegisteredError()

    with open(domain_name_file) as dnf:
        lazy_domain_name = dnf.read().rstrip()
        return lazy_domain_name


version = 1

_description = [
    _('diaspora* is a decentralized social network where you can store '
      'and control your own data.'),
    format_lazy(
        'When enabled, the diaspora* pod will be available from '
        '<a href="https://diaspora.{host}">diaspora.{host}</a> path on the '
        'web server.'.format(host=get_configured_domain_name()) if is_setup()
        else 'Please register a domain name for your FreedomBox to be able to'
        ' federate with other diaspora* pods.')
]

app = None


class DiasporaApp(app_module.App):
    """FreedomBox app for Diaspora."""

    app_id = 'diaspora'

    def __init__(self):
        """Create components for the app."""
        super().__init__()
        from . import manifest

        info = app_module.Info(app_id=self.app_id, version=version,
                               name=_('diaspora*'), icon_filename='diaspora',
                               short_description=_('Federated Social Network'),
                               description=_description,
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-diaspora', info.name,
                              info.short_description, info.icon_filename,
                              'diaspora:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = Shortcut('shortcut-diaspora', info.name,
                            short_description=info.short_description,
                            icon=info.icon_filename, url=None,
                            clients=info.clients, login_required=True)
        self.add(shortcut)

        packages = Packages('packages-diaspora', ['diaspora'])
        self.add(packages)

        firewall = Firewall('firewall-diaspora', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-diaspora', 'diaspora-plinth')
        self.add(webserver)

        daemon = Daemon('daemon-diaspora', 'diaspora')
        self.add(daemon)

    def diagnose(self):
        """Run diagnostics and return the results."""
        results = super().diagnose()

        results.append(
            diagnose_url('http://diaspora.localhost', kind='4',
                         check_certificate=False))
        results.append(
            diagnose_url('http://diaspora.localhost', kind='6',
                         check_certificate=False))
        results.append(
            diagnose_url(
                'http://diaspora.{}'.format(get_configured_domain_name()),
                kind='4', check_certificate=False))

        return results


class Shortcut(frontpage.Shortcut):
    """Frontpage shortcut to use configured domain name for URL."""

    def enable(self):
        """Set the proper shortcut URL when enabled."""
        super().enable()
        self.url = 'https://diaspora.{}'.format(get_configured_domain_name())


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.call('pre', actions.superuser_run, 'diaspora', ['pre-install'])
    app.setup(old_version)
    helper.call('custom_config', actions.superuser_run, 'diaspora',
                ['disable-ssl'])


def setup_domain_name(domain_name):
    actions.superuser_run('diaspora', ['setup', '--domain-name', domain_name])
    app.enable()


def is_user_registrations_enabled():
    """Return whether user registrations are enabled"""
    with open('/etc/diaspora/diaspora.yml') as f:
        for line in f.readlines():
            if "enable_registrations" in line:
                return line.split(":")[1].strip() == "true"


def enable_user_registrations():
    """Allow users to register without invitation"""
    actions.superuser_run('diaspora', ['enable-user-registrations'])


def disable_user_registrations():
    """Disallow users from registering without invitation"""
    actions.superuser_run('diaspora', ['disable-user-registrations'])


def generate_apache_configuration(conf_file, domain_name):
    """Generate Diaspora's apache configuration with the given domain name"""
    open(conf_file, 'w').close()

    diaspora_domain_name = ".".join(["diaspora", domain_name])

    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)

    aug.set('/augeas/load/Httpd/lens', 'Httpd.lns')
    aug.set('/augeas/load/Httpd/incl[last() + 1]', conf_file)
    aug.load()

    aug.defvar('conf', '/files' + conf_file)

    aug.set('$conf/VirtualHost', None)
    aug.defvar('vh', '$conf/VirtualHost')
    aug.set('$vh/arg', diaspora_domain_name)
    aug.set('$vh/directive[1]', 'ServerName')
    aug.set('$vh/directive[1]/arg', diaspora_domain_name)
    aug.set('$vh/directive[2]', 'DocumentRoot')
    aug.set('$vh/directive[2]/arg', '"/var/lib/diaspora/public/"')

    aug.set('$vh/Location', None)
    aug.set('$vh/Location/arg', '"/"')
    aug.set('$vh/Location/directive[1]', 'ProxyPass')
    aug.set('$vh/Location/directive[1]/arg',
            '"unix:/var/run/diaspora/diaspora.sock|http://localhost/"')

    aug.set('$vh/Location[last() + 1]', None)
    aug.set('$vh/Location[last()]/arg', '"/assets"')
    aug.set('$vh/Location[last()]/directive[1]', 'ProxyPass')
    aug.set('$vh/Location[last()]/directive[1]/arg', '!')

    aug.set('$vh/Directory', None)
    aug.set('$vh/Directory/arg', '/var/lib/diaspora/public/')
    aug.set('$vh/Directory/directive[1]', 'Require')
    aug.set('$vh/Directory/directive[1]/arg[1]', 'all')
    aug.set('$vh/Directory/directive[1]/arg[2]', 'granted')

    aug.save()
