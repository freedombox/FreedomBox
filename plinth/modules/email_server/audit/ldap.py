# SPDX-License-Identifier: AGPL-3.0-or-later
import plinth.modules.email_server.postconf as postconf
from . import models

default_config = {
    'smtpd_sasl_auth_enable': 'yes',
    'smtpd_sasl_type': 'dovecot',
    'smtpd_sasl_path': 'private/auth'
}


# GET /audit/domain
def get():
    """Compare current values with the default. Generate an audit report"""
    results = models.Result('LDAP for user accounts')
    current_config = postconf.get_many(list(default_config.keys()))
    for key, value in default_config.items():
        if current_config[key] != value:
            results.fails.append('{} should equal {}'.format(key, value))
    return results


# POST /audit/domain/repair
def repair():
    postconf.set_many(default_config)
