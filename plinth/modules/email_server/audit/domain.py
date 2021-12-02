"""Configure email domains"""
# SPDX-License-Identifier: AGPL-3.0-or-later

import pathlib
import re
import subprocess

from plinth.actions import superuser_run
from plinth.modules import config
from plinth.modules.email_server import postconf
from plinth.modules.names.components import DomainName


def get_domains():
    """Return the current domain configuration."""
    conf = postconf.get_many(['mydomain', 'mydestination'])
    domains = set(postconf.parse_maps(conf['mydestination']))
    defaults = {'$myhostname', 'localhost.$mydomain', 'localhost'}
    domains.difference_update(defaults)
    return {'primary_domain': conf['mydomain'], 'all_domains': domains}


def set_domains(primary_domain=None):
    """Set the primary domain and all the domains for postfix. """
    all_domains = DomainName.list_names()
    if not primary_domain:
        primary_domain = get_domains()['primary_domain']
        if primary_domain not in all_domains:
            primary_domain = config.get_domainname() or list(all_domains)[0]

    superuser_run(
        'email_server',
        ['domain', 'set_domains', primary_domain, ','.join(all_domains)])


def action_set_domains(primary_domain, all_domains):
    """Set the primary domain and all the domains for postfix. """
    all_domains = [_clean_domain(domain) for domain in all_domains.split(',')]
    primary_domain = _clean_domain(primary_domain)

    defaults = {'$myhostname', 'localhost.$mydomain', 'localhost'}
    all_domains = set(all_domains).union(defaults)
    conf = {
        'myhostname': primary_domain,
        'mydomain': primary_domain,
        'mydestination': ', '.join(all_domains)
    }
    postconf.set_many(conf)
    pathlib.Path('/etc/mailname').write_text(primary_domain + '\n')
    subprocess.run(['systemctl', 'try-reload-or-restart', 'postfix'],
                   check=True)


def _clean_domain(domain):
    domain = domain.lower().strip()
    assert re.match('^[a-z0-9-\\.]+$', domain)
    return domain
