# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for the LDAP user directory."""

import logging
import os
import pathlib
import re
import shutil
import subprocess

import augeas

from plinth import action_utils, utils
from plinth.actions import privileged, secret_str

INPUT_LINES = None
ACCESS_CONF = '/etc/security/access.conf'
LDAPSCRIPTS_CONF = '/etc/ldapscripts/freedombox-ldapscripts.conf'


def _validate_user(username, password, must_be_admin=True):
    """Validate a user."""
    if must_be_admin:
        admins = _get_admin_users()

        if not admins:
            # any user is valid
            return

        if not username:
            raise PermissionError('Authentication user is required')

        if username not in admins:
            msg = f'"{username}" is not authorized to perform this action'
            raise PermissionError(msg)

    if not username:
        raise PermissionError('Authentication user is required')

    _validate_password(username, password)


def _validate_password(username, password):
    """Raise an error if the user password is invalid."""
    if not utils.is_authenticated_user(username, password):
        raise PermissionError('Invalid credentials')


def _validate_username(username):
    """Validate username."""
    if pathlib.Path(username).parts[-1] != username:
        raise ValueError('Invalid username')


@privileged
def first_setup():
    """Perform initial setup of LDAP."""
    # Avoid reconfiguration of slapd during module upgrades, because
    # this will move the existing database.
    # XXX: Instead of a separate action that is conditionally called for a
    # version number, we can check if the domain currently configured is what
    # we want and then based on the value do a reconfiguration. This approach
    # will work better when FreedomBox state is reset etc.
    action_utils.dpkg_reconfigure('slapd', {'domain': 'thisbox'})


@privileged
def setup():
    """Setup LDAP."""
    # Update pam config for mkhomedir.
    subprocess.run(['pam-auth-update', '--package'], check=True)

    _configure_ldapscripts()

    _configure_ldap_authentication()

    _configure_ldap_structure()


@privileged
def setup_and_sync_user_states(inactivated_users: list[str]):
    """Setup password policy and inactivate users."""
    _create_organizational_unit('policies')
    first_ppolicy_setup = _setup_ldap_ppolicy()

    if first_ppolicy_setup and inactivated_users:
        _upgrade_inactivate_users(inactivated_users)


def _configure_ldap_authentication():
    """Configure LDAP authentication."""
    action_utils.dpkg_reconfigure(
        'nslcd', {
            'ldap-uris': 'ldapi:///',
            'ldap-base': 'dc=thisbox',
            'ldap-auth-type': 'SASL',
            'ldap-sasl-mech': 'EXTERNAL'
        })

    # Set nslcd authorization filter for user locking
    authorization_filter = ('(&(objectClass=posixAccount)(uid=$username)'
                            '(!(pwdAccountLockedTime=000001010000Z)))')
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Nslcd/lens', 'Nslcd.lns')
    aug.set('/augeas/load/Nslcd/incl[last() + 1]', '/etc/nslcd.conf')
    aug.load()
    aug.set('/files/etc/nslcd.conf/pam_authz_search', authorization_filter)
    aug.save()

    action_utils.dpkg_reconfigure('libnss-ldapd',
                                  {'nsswitch': 'group, passwd, shadow'})

    # NSS caching is not necessary in FreedomBox as lookup are done on a local
    # LDAP daemon. Caching can lead to unexpected behavior after user account
    # changes and after queries while nslcd is not running. See:
    # https://salsa.debian.org/freedombox-team/freedombox/-/merge_requests/2520
    action_utils.service_mask('nscd')
    action_utils.service_stop('nscd')
    action_utils.service_mask('unscd')
    action_utils.service_stop('unscd')

    # XXX: Workaround for login issue
    action_utils.service_enable('slapd')
    action_utils.service_start('slapd')
    action_utils.service_enable('nslcd')
    # For changes in /etc/nslcd.conf to take effect, restart the service
    action_utils.service_restart('nslcd')


def _configure_ldap_structure():
    """Configure LDAP basic structure."""
    was_running = action_utils.service_is_running('slapd')
    if not was_running:
        action_utils.service_start('slapd')

    _setup_admin()
    _create_organizational_unit('users')
    _create_organizational_unit('groups')
    _create_organizational_unit('policies')
    _setup_ldap_ppolicy()


def _create_organizational_unit(unit):
    """Create an organizational unit in LDAP."""
    distinguished_name = 'ou={unit},dc=thisbox'.format(unit=unit)
    try:
        subprocess.run([
            'ldapsearch', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///', '-s',
            'base', '-b', distinguished_name, '(objectclass=*)'
        ], stdout=subprocess.DEVNULL, check=True)
        return  # Already exists
    except subprocess.CalledProcessError:
        input = '''
dn: ou={unit},dc=thisbox
objectClass: top
objectClass: organizationalUnit
ou: {unit}'''.format(unit=unit)
        subprocess.run(['ldapadd', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
                       input=input.encode(), stdout=subprocess.DEVNULL,
                       check=True)


def _setup_admin():
    """Remove LDAP admin password and Allow root to modify the users."""
    process = subprocess.run([
        'ldapsearch', '-Q', '-L', '-L', '-L', '-Y', 'EXTERNAL', '-H',
        'ldapi:///', '-s', 'base', '-b', 'olcDatabase={1}mdb,cn=config',
        '(objectclass=*)', 'olcRootDN', 'olcRootPW'
    ], check=True, stdout=subprocess.PIPE)
    ldap_object = {}
    for line in process.stdout.decode().splitlines():
        if line:
            line = line.split(':')
            ldap_object[line[0]] = line[1]

    if 'olcRootPW' in ldap_object:
        subprocess.run(
            ['ldapmodify', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
            check=True, stdout=subprocess.DEVNULL, input=b'''
dn: olcDatabase={1}mdb,cn=config
changetype: modify
delete: olcRootPW''')

    root_dn = 'gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth'
    if ldap_object['olcRootDN'] != root_dn:
        subprocess.run(
            ['ldapmodify', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
            check=True, stdout=subprocess.DEVNULL, input=b'''
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcRootDN
olcRootDN: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
''')


def _setup_ldap_ppolicy() -> bool:
    """Setup default password policy for user accounts.

    The default password policy makes passwords lockable. Users who have
    the LDAP operational attribute pwdAccountLockedTime=000001010000Z can't
    login with password.

    Returns whether it was the first run that enables this policy.
    """
    # Load ppolicy module
    try:
        subprocess.run(
            ['ldapmodify', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
            check=True, stdout=subprocess.DEVNULL, input=b'''
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: ppolicy''')
    except subprocess.CalledProcessError as error:
        if error.returncode != 20:  # Value already exists
            raise

    # Add namedobject schema needed for 'objectClass: namedPolicy'.
    try:
        subprocess.run([
            'ldapadd', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///', '-f',
            '/etc/ldap/schema/namedobject.ldif'
        ], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as error:
        if error.returncode != 80:  # Schema already added
            raise

    # Set up default password policy
    try:
        subprocess.run(['ldapadd', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
                       check=True, stdout=subprocess.DEVNULL, input=b'''
dn: cn=DefaultPPolicy,ou=policies,dc=thisbox
cn: DefaultPPolicy
objectClass: pwdPolicy
objectClass: namedPolicy
objectClass: top
pwdAttribute: userPassword
pwdLockout: TRUE''')
    except subprocess.CalledProcessError as error:
        if error.returncode != 68:  # Value already exists
            raise

    # Make DefaultPPolicy as a default ppolicy overlay
    try:
        subprocess.run(['ldapadd', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///'],
                       check=True, stdout=subprocess.DEVNULL, input=b'''
dn: olcOverlay={0}ppolicy,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcPPolicyConfig
olcOverlay: {0}ppolicy
olcPPolicyDefault: cn=DefaultPPolicy,ou=policies,dc=thisbox
''')
    except subprocess.CalledProcessError as error:
        if error.returncode == 80:  # Value already in list
            return False
        else:
            raise

    return True


def _configure_ldapscripts():
    """Set the configuration used by ldapscripts for later user management."""
    # modify a copy of the config file
    shutil.copy('/etc/ldapscripts/ldapscripts.conf', LDAPSCRIPTS_CONF)

    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.set('/augeas/load/Shellvars/lens', 'Shellvars.lns')
    aug.set('/augeas/load/Shellvars/incl[last() + 1]', LDAPSCRIPTS_CONF)
    aug.load()

    # XXX: Password setting on users is disabled as changing passwords
    # using SASL Auth is not supported.
    aug.set('/files' + LDAPSCRIPTS_CONF + '/SERVER', '"ldapi://"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/SASLAUTH', '"EXTERNAL"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/SUFFIX', '"dc=thisbox"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/USUFFIX', '"ou=Users"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/GSUFFIX', '"ou=Groups"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/PASSWORDGEN', '"true"')
    aug.set('/files' + LDAPSCRIPTS_CONF + '/CREATEHOMES', '"yes"')
    aug.save()


def _lock_ldap_user(username: str):
    """Lock user."""
    if not _user_exists(username):
        return None

    # Replace command adds the attribute if it doesn't exist.
    input = '''changetype: modify
replace: pwdAccountLockedTime
pwdAccountLockedTime: 000001010000Z
'''
    _run(['ldapmodifyuser', username], input=input.encode())


def _unlock_ldap_user(username: str):
    """Unlock user."""
    if not _user_exists(username):
        return None

    # Replace command without providing a value will remove the attribute
    # and ignores when the attribute doesn't exist.
    input = '''changetype: modify
replace: pwdAccountLockedTime
'''
    _run(['ldapmodifyuser', username], input=input.encode())


@privileged
def get_nslcd_config() -> dict[str, str]:
    """Get nslcd configuration for diagnostics."""
    nslcd_conf = '/etc/nslcd.conf'
    aug = augeas.Augeas(flags=augeas.Augeas.NO_LOAD +
                        augeas.Augeas.NO_MODL_AUTOLOAD)
    aug.transform('Nslcd', nslcd_conf)
    aug.set('/augeas/context', '/files' + nslcd_conf)
    aug.load()

    return {
        'uri': aug.get('uri/1'),
        'base': aug.get('base'),
        'sasl_mech': aug.get('sasl_mech')
    }


def _get_samba_users():
    """Get users from the Samba user database."""
    # 'pdbedit -L' is better for listing users but is installed only with samba
    stdout = subprocess.check_output(
        ['tdbdump', '/var/lib/samba/private/passdb.tdb']).decode()
    return re.findall(r'USER_(.*)\\0', stdout)


def _delete_samba_user(username):
    """Delete a Samba user."""
    if username in _get_samba_users():
        subprocess.check_call(['smbpasswd', '-x', username])
        _disconnect_samba_user(username)


def _disconnect_samba_user(username):
    """Disconnect a Samba user."""
    try:
        subprocess.check_call(['pkill', '-U', username, 'smbd'])
    except subprocess.CalledProcessError as error:
        if error.returncode != 1:
            raise


def _get_user_home(username):
    """Return the user home directory."""
    output = subprocess.check_output(['getent', 'passwd', username], text=True)
    return pathlib.Path(output.split(':')[5])


@privileged
def create_user(username: str, password: secret_str,
                auth_user: str | None = None,
                auth_password: secret_str | None = None):
    """Create an LDAP user, set password and flush cache."""
    _validate_username(username)
    _validate_user(auth_user, auth_password)

    _run(['ldapadduser', username, 'users'])

    _set_user_password(username, password)
    _flush_cache()
    _set_samba_user(username, password)


@privileged
def remove_user(username: str, auth_user: str, auth_password: secret_str):
    """Remove an LDAP user."""
    _validate_username(username)
    _validate_user(auth_user, auth_password)
    groups = _get_user_groups(username)

    _delete_samba_user(username)

    for group in groups:
        _remove_user_from_group(username, group)

    if _user_exists(username):
        # remove the home folder if it's owned by the user
        home_folder = _get_user_home(username)
        if home_folder.is_dir():
            try:
                owner = home_folder.owner()
            except KeyError:  # owner not found
                pass
            else:
                if owner == username:
                    shutil.rmtree(home_folder, ignore_errors=True)

        _run(['ldapdeleteuser', username])

    _flush_cache()


def _rename_ldap_user(old_username: str, new_username: str,
                      new_home: pathlib.Path | None):
    """Rename LDAP user and user parameters."""
    _run(['ldaprenameuser', old_username, new_username])

    input = f'''changetype: modify
replace: cn
cn: {new_username}
-
replace: gecos
gecos: {new_username}
'''

    if new_home:
        input += f'''-
replace: homeDirectory
homeDirectory: {str(new_home)}
'''

    _run(['ldapmodifyuser', new_username], input=input.encode())


@privileged
def rename_user(old_username: str, new_username: str):
    """Rename an LDAP user."""
    _validate_username(old_username)
    _validate_username(new_username)
    groups = _get_user_groups(old_username)

    _delete_samba_user(old_username)

    for group in groups:
        _remove_user_from_group(old_username, group)

    old_home = _get_user_home(old_username)
    new_home = old_home.with_name(new_username)

    if new_home.exists():
        new_home = None  # Do not rename home
    else:
        if old_home.is_dir():
            old_home.rename(new_home)

    _rename_ldap_user(old_username, new_username, new_home)

    for group in groups:
        _add_user_to_group(new_username, group)

    _flush_cache()


def _set_user_password(username, password):
    """Set a user's password."""
    process = _run(['slappasswd', '-s', password], stdout=subprocess.PIPE)
    password = process.stdout.decode().strip()
    _run(['ldapsetpasswd', username, password])


def _set_samba_user(username, password):
    """Insert a user to the Samba database.

    If a user already exists, update password.
    """
    proc = subprocess.run(['smbpasswd', '-a', '-s', username],
                          input='{0}\n{0}\n'.format(password).encode(),
                          stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise RuntimeError('Unable to add Samba user: ', proc.stderr)


@privileged
def set_user_password(username: str, password: secret_str, auth_user: str,
                      auth_password: secret_str):
    """Set a user's password."""
    must_be_admin = username != auth_user
    _validate_user(auth_user, auth_password, must_be_admin=must_be_admin)

    _set_user_password(username, password)
    _set_samba_user(username, password)


def _get_admin_users():
    """Return list of members in the admin group.

    Raise an error if the slapd service is not running.
    """
    admin_users = []

    try:
        output = subprocess.check_output([
            'ldapsearch', '-LLL', '-Q', '-Y', 'EXTERNAL', '-H', 'ldapi:///',
            '-o', 'ldif-wrap=no', '-s', 'base', '-b',
            'cn=admin,ou=groups,dc=thisbox', 'memberUid'
        ]).decode()
    except subprocess.CalledProcessError as error:
        if error.returncode == 32:
            # no entries found
            return []
        raise

    for line in output.splitlines():
        if line.startswith('memberUid: '):
            user = line.split('memberUid: ', 1)[1].strip()
            admin_users.append(user)

    return admin_users


def _get_user_ids(username: str) -> str | None:
    """Get user information in format like `id` command."""
    try:
        process = _run(['ldapid', username], stdout=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        if error.returncode == 1:
            # User doesn't exist
            return None

        raise

    return process.stdout.decode().strip()


def _user_exists(username):
    """Return whether the user exists."""
    return _get_user_ids(username) is not None


def _get_group_users(groupname):
    """Return list of members in the group."""
    try:
        process = _run(['ldapgid', '-P', groupname], stdout=subprocess.PIPE)
    except subprocess.CalledProcessError:
        return []  # Group does not exist

    output = process.stdout.decode()
    # extract users from output, example: 'admin:*:10001:user1,user2'
    users = output.rsplit(':')[-1].strip().split(',')
    if users == ['']:
        return []
    return users


def _get_user_groups(username):
    """Return only the supplementary groups of the given user.

    Exclude the 'users' primary group from the returned list.
    """
    output = _get_user_ids(username)
    if output:
        groups_part = output.split(' ')[2]
        try:
            groups = groups_part.split('=')[1]
        except IndexError:
            logging.warning('Could not read groups for user %s: \n%s',
                            username, output)
            return []

        group_names = [
            user.strip('()') for user in re.findall(r'\(.*?\)', groups)
        ]
        group_names.remove('users')
        return group_names

    logging.warning('User %s not found in LDAP', username)
    return []


@privileged
def get_user_groups(username: str) -> list[str]:
    """Return list of a given user's groups."""
    return _get_user_groups(username)


def _group_exists(groupname):
    """Return whether a group already exits."""
    process = _run(['ldapgid', groupname], check=False)
    return process.returncode == 0


def _create_group(groupname):
    """Add an LDAP group."""
    if not _group_exists(groupname):
        _run(['ldapaddgroup', groupname])


@privileged
def create_group(groupname: str):
    """Add an LDAP group."""
    _create_group(groupname)
    _flush_cache()


@privileged
def rename_group(old_groupname: str, new_groupname: str):
    """Rename an LDAP group.

    Skip if the group to rename from doesn't exist.
    """
    if old_groupname == 'admin' or new_groupname == 'admin':
        raise ValueError('Can\'t rename the group "admin"')

    if _group_exists(old_groupname):
        _run(['ldaprenamegroup', old_groupname, new_groupname])
        _flush_cache()


@privileged
def remove_group(groupname: str):
    """Remove an LDAP group."""
    if groupname == 'admin':
        raise ValueError("Can't remove the group 'admin'")

    if _group_exists(groupname):
        _run(['ldapdeletegroup', groupname])
        _flush_cache()


def _add_user_to_group(username, groupname):
    """Add an LDAP user to an LDAP group."""
    _create_group(groupname)
    _run(['ldapaddusertogroup', username, groupname])


@privileged
def add_user_to_group(username: str, groupname: str,
                      auth_user: str | None = None,
                      auth_password: secret_str | None = None):
    """Add an LDAP user to an LDAP group."""
    if groupname == 'admin':
        _validate_user(auth_user, auth_password)

    _add_user_to_group(username, groupname)
    _flush_cache()


def _remove_user_from_group(username, groupname):
    """Remove an LDAP user from an LDAP group."""
    _run(['ldapdeleteuserfromgroup', username, groupname])


@privileged
def remove_user_from_group(username: str, groupname: str, auth_user: str,
                           auth_password: secret_str):
    """Remove an LDAP user from an LDAP group."""
    if groupname == 'admin':
        _validate_user(auth_user, auth_password)

    _remove_user_from_group(username, groupname)
    _flush_cache()
    if groupname == 'freedombox-share':
        _disconnect_samba_user(username)


@privileged
def get_group_users(group_name: str) -> list[str]:
    """Get the list of users of an LDAP group."""
    return _get_group_users(group_name)


@privileged
def set_user_status(username: str, status: str, auth_user: str,
                    auth_password: secret_str):
    """Set the status of the user."""
    if status not in ('active', 'inactive'):
        raise ValueError('Invalid status')

    _validate_user(auth_user, auth_password)

    if status == 'active':
        _unlock_ldap_user(username)
        smbpasswd_flag = '-e'
    else:
        _lock_ldap_user(username)
        smbpasswd_flag = '-d'

    # Set user status in Samba password database
    if username in _get_samba_users():
        subprocess.check_call(['smbpasswd', smbpasswd_flag, username])

    _flush_cache()

    if status == 'inactive':
        # Kill all user processes. This includes disconnectiong ssh, samba and
        # cockpit sessions.
        subprocess.run(['pkill', '--signal', 'KILL', '--uid', username])


def _upgrade_inactivate_users(usernames: list[str]):
    """Inactivate users in LDAP."""
    for username in usernames:
        _lock_ldap_user(username)

    _flush_cache()

    for username in usernames:
        subprocess.run(['pkill', '--signal', 'KILL', '--uid', username])


def _flush_cache():
    """Flush apache2 cache."""
    action_utils.service_reload('apache2')


def _run(arguments, check=True, **kwargs):
    """Run a command. Check return code and suppress output by default."""
    env = dict(os.environ, LDAPSCRIPTS_CONF=LDAPSCRIPTS_CONF)
    kwargs['stdout'] = kwargs.get('stdout', subprocess.DEVNULL)
    kwargs['stderr'] = kwargs.get('stderr', subprocess.DEVNULL)
    return subprocess.run(arguments, env=env, check=check, **kwargs)
