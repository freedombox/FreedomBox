# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Configure domains accepted by postfix.

See: http://www.postfix.org/postconf.5.html#mydestination
See: http://www.postfix.org/postconf.5.html#mydomain
See: http://www.postfix.org/postconf.5.html#myhostname
"""

import pathlib
import re

from plinth.actions import privileged
from plinth.app import App
from plinth.modules import names
from plinth.modules.email import postfix
from plinth.modules.names.components import DomainName

from . import dkim, tls


def get_domains():
    """Return the current domain configuration."""
    conf = postfix.get_config(['mydomain', 'mydestination'])
    domains = set(postfix.parse_maps(conf['mydestination']))
    defaults = {'$myhostname', 'localhost.$mydomain', 'localhost'}
    domains.difference_update(defaults)
    return {'primary_domain': conf['mydomain'], 'all_domains': domains}


def set_all_domains(primary_domain=None):
    """Set the primary domain and all the domains for postfix."""
    all_domains = DomainName.list_names()
    if not primary_domain:
        primary_domain = get_domains()['primary_domain']
        if primary_domain not in all_domains:
            primary_domain = names.get_domain_name() or list(all_domains)[0]

    # Update configuration and don't restart daemons
    set_domains(primary_domain, list(all_domains))
    for domain in all_domains:
        dkim.setup_dkim(domain)

    # Copy certificates (self-signed if needed) and restart daemons
    app = App.get('email')
    app.get_component('letsencrypt-email-postfix').setup_certificates()
    app.get_component('letsencrypt-email-dovecot').setup_certificates()


@privileged
def set_domains(primary_domain: str, all_domains: list[str]):
    """Set the primary domain and all the domains for postfix."""
    all_domains = [_clean_domain(domain) for domain in all_domains]
    primary_domain = _clean_domain(primary_domain)

    defaults = {'$myhostname', 'localhost.$mydomain', 'localhost'}
    my_destination = ', '.join(set(all_domains).union(defaults))
    conf = {
        'myhostname': primary_domain,
        'mydomain': primary_domain,
        'mydestination': my_destination
    }
    postfix.set_config(conf)
    pathlib.Path('/etc/mailname').write_text(primary_domain + '\n',
                                             encoding='utf-8')
    tls.set_postfix_config(primary_domain, all_domains)
    tls.set_dovecot_config(primary_domain, all_domains)


def _clean_domain(domain):
    domain = domain.lower().strip()
    assert re.match('^[a-z0-9-\\.]+$', domain)
    return domain
