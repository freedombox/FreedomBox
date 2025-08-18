# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure SOGo."""

import pathlib
import re
import shutil
import tempfile

from plinth import action_utils, utils
from plinth.actions import privileged
from plinth.db import postgres
from plinth.modules.email.privileged.domain import \
    get_domains as get_email_domains

DB_HOST = 'localhost'
DB_NAME = 'sogo_fbx'
DB_USER = 'sogo_fbx'
SERVICE_NAME = 'sogo'

DB_BACKUP_FILE = pathlib.Path('/var/lib/plinth/backups-data/sogo-database.sql')
CONFIG_FILE = pathlib.Path('/etc/sogo/sogo.conf')


@privileged
def setup() -> None:
    """Setup SOGo database and configuration."""
    database_password = utils.generate_password(16)
    postgres.create_database(DB_NAME, DB_USER, database_password)
    _create_config(database_password)


def _create_config(db_password: str):
    """Configure /etc/sogo/sogo.conf"""
    try:
        domain = _get_config_value('SOGoMailDomain')
        if not domain:
            # Try to get the domain configured for the email app
            domain = get_email_domains()['primary_domain']
    except FileNotFoundError:
        domain = 'localhost'

    connection = f'postgresql://{DB_USER}:{db_password}@{DB_HOST}/{DB_NAME}'

    content = f'''
{{
  /* General */
  SOGoMailDomain = "{domain}";
  SOGoLanguage = "English";
  SOGoTimeZone = "UTC";
  SOGoCalendarDefaultRoles = ("PublicViewer", "ConfidentialDAndTViewer");
  SOGoAppointmentSendEMailNotifications = YES;
  SOGoRefreshViewCheck = "every_minute";
  /* Allow users to add their own additional IMAP accounts */
  SOGoMailAuxiliaryUserAccountsEnabled = YES;
  /* Allow users to change their full name in default account */
  SOGoMailCustomFromEnabled = YES;

  /* Authentication */
  SOGoMaximumFailedLoginCount = "10";
  SOGoMaximumFailedLoginInterval = "300";
  SOGoFailedLoginBlockInterval = "300";

  /* Database */
  SOGoProfileURL = "{connection}/sogo_user_profile";
  OCSFolderInfoURL = "{connection}/sogo_folder_info";
  OCSSessionsFolderURL = "{connection}/sogo_sessions_folder";
  OCSEMailAlarmsFolderURL = "{connection}/sogo_alarms_folder";
  OCSStoreURL = "{connection}/sogo_store";
  OCSAclURL = "{connection}/sogo_acl";
  OCSCacheFolderURL = "{connection}/sogo_cache_folder";
  OCSAdminURL = "{connection}/sogo_admin";

  /* Cache */
  SOGoMemcachedHost = "127.0.0.1";

  /* SMTP */
  SOGoMailingMechanism = "smtp";
  SOGoSMTPServer = "smtp://127.0.0.1:587/?tls=YES&tlsVerifyMode=allowInsecureLocalhost";
  SOGoSMTPAuthenticationType = "PLAIN";

  /* IMAP */
  SOGoDraftsFolderName = "Drafts";
  SOGoSentFolderName = "Sent";
  SOGoTrashFolderName = "Trash";
  SOGoJunkFolderName = "Junk";
  SOGoIMAPServer = "imap://127.0.0.1:143/?tls=YES&tlsVerifyMode=allowInsecureLocalhost";
  SOGoSieveServer = "sieve://127.0.0.1:4190/?tls=YES&tlsVerifyMode=allowInsecureLocalhost";

  /* LDAP */
  SOGoUserSources = ({{
    type = "ldap";
    CNFieldName = "cn";
    IDFieldName = "uid";
    UIDFieldName = "uid";
    baseDN = "ou=users,dc=thisbox";
    canAuthenticate = YES;
    displayName = "Shared Addresses";
    hostname = "ldap://127.0.0.1:389";
    id = "directory";
    isAddressBook = YES;
  }});
}}'''  # noqa: E501
    CONFIG_FILE.touch(0o640, exist_ok=True)  # In case the file does not exist
    CONFIG_FILE.chmod(0o640)  # In case the file pre-existed
    shutil.chown(CONFIG_FILE, 'root', 'sogo')
    CONFIG_FILE.write_text(content, encoding='utf-8')


@privileged
def dump_database() -> None:
    """Dump database to file."""
    postgres.dump_database(DB_BACKUP_FILE, DB_NAME)


@privileged
def restore_database() -> None:
    """Restore database from file."""
    password = _read_db_password()
    postgres.restore_database(DB_BACKUP_FILE, DB_NAME, DB_USER, password)


def _read_db_password() -> str:
    """Extract the database password from /etc/sogo/sogo.conf using regex"""
    pattern = r'postgresql://[^:]+:([^@]+)@localhost'
    match = re.search(pattern, _get_config_value('SOGoProfileURL'))
    if not match:
        raise ValueError('Could not extract password')

    return match.group(1)


@privileged
def get_domain() -> str:
    """Get the value of SOGoMailDomain from /etc/sogo/sogo.conf"""
    return _get_config_value('SOGoMailDomain')


@privileged
def set_domain(domain: str):
    """Set the value of SOGoMailDomain in /etc/sogo/sogo.conf"""
    _set_config_value('SOGoMailDomain', domain)


def _get_config_value(key: str) -> str:
    """Return the value of a property from the configuration file."""
    process = action_utils.run(['plget', key], input=CONFIG_FILE.read_bytes(),
                               check=True)
    return process.stdout.decode().strip()


def _set_config_value(key: str, value: str):
    """Set the value of a property in the configuration file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(f'{{\n{key} = "{value}";\n}}'.encode('utf-8'))
        temp_file.close()
        action_utils.run(['plmerge', CONFIG_FILE, temp_file.name], check=True)
        pathlib.Path(temp_file.name).unlink()


@privileged
def uninstall() -> None:
    """Uninstall SOGo: drop database and configuration files."""
    postgres.drop_database(DB_NAME, DB_USER)
    CONFIG_FILE.unlink(missing_ok=True)
