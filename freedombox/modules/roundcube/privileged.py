# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure roundcube."""

import pathlib
import re

from plinth import action_utils
from plinth.actions import privileged

_config_file = pathlib.Path('/etc/roundcube/freedombox-config.php')
_rc_db_file = pathlib.Path('/var/lib/dbconfig-common/sqlite3/'
                           'roundcube/roundcube')


@privileged
def pre_install():
    """Preseed debconf values before packages are installed."""
    action_utils.debconf_set_selections([
        'roundcube-core roundcube/dbconfig-install boolean true',
        'roundcube-core roundcube/database-type string sqlite3'
    ])


@privileged
def setup():
    """Add FreedomBox configuration and include from main configuration."""
    if not _config_file.exists():
        _config_file.write_text('<?php\n', encoding='utf-8')

    base_config = pathlib.Path('/etc/roundcube/config.inc.php')
    lines = base_config.read_text(encoding='utf-8').splitlines()
    exists = any((str(_config_file) in line for line in lines))
    if not exists:
        lines.append(f'include_once("{_config_file}");\n')
        base_config.write_text('\n'.join(lines), encoding='utf-8')


@privileged
def get_config() -> dict[str, bool]:
    """Return the current configuration as a dictionary."""
    pattern = r'\s*\$config\[\s*\'([^\']*)\'\s*\]\s*=\s*\'([^\']*)\'\s*;'
    _config = {}
    try:
        for line in _config_file.read_text(encoding='utf-8').splitlines():
            match = re.match(pattern, line)
            if match:
                _config[match.group(1)] = match.group(2)
    except FileNotFoundError:
        pass

    local_only = _config.get('default_host') == 'localhost'
    return {'local_only': local_only}


@privileged
def set_config(local_only: bool):
    """Set the configuration."""
    config = '''<?php
$config['log_driver'] = 'syslog';
'''

    if local_only:
        config += '''
$config['default_host'] = 'localhost';
$config['mail_domain'] = '%n';

$config['smtp_server'] = 'localhost';
$config['smtp_port'] = 25;
$config['smtp_helo_host'] = 'localhost';
'''

    _config_file.write_text(config, encoding='utf-8')


@privileged
def uninstall():
    """Remove config file and database."""
    for item in _config_file, _rc_db_file:
        item.unlink(missing_ok=True)
