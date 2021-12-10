# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app to configure Gitweb.
"""

import json
import os

from django.utils.translation import gettext_lazy as _

from plinth import actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.errors import ActionError
from plinth.modules.apache.components import Webserver
from plinth.modules.backups.components import BackupRestore
from plinth.modules.firewall.components import Firewall
from plinth.modules.users.components import UsersAndGroups
from plinth.package import Packages

from . import manifest
from .forms import is_repo_url
from .manifest import GIT_REPO_PATH

_description = [
    _('Git is a distributed version-control system for tracking changes in '
      'source code during software development. Gitweb provides a web '
      'interface to Git repositories. You can browse history and content of '
      'source code, use search to find relevant commits and code. '
      'You can also clone repositories and upload code changes with a '
      'command-line Git client or with multiple available graphical clients. '
      'And you can share your code with people around the world.'),
    _('To learn more on how to use Git visit '
      '<a href="https://git-scm.com/docs/gittutorial">Git tutorial</a>.')
]

app = None


class GitwebApp(app_module.App):
    """FreedomBox app for Gitweb."""

    app_id = 'gitweb'

    _version = 1

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        groups = {'git-access': _('Read-write access to Git repositories')}

        self.repos = []

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               name=_('Gitweb'), icon_filename='gitweb',
                               short_description=_('Simple Git Hosting'),
                               description=_description, manual_page='GitWeb',
                               clients=manifest.clients)
        self.add(info)

        menu_item = menu.Menu('menu-gitweb', info.name, info.short_description,
                              info.icon_filename, 'gitweb:index',
                              parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-gitweb', info.name,
                                      short_description=info.short_description,
                                      icon=info.icon_filename, url='/gitweb/',
                                      clients=info.clients,
                                      login_required=True,
                                      allowed_groups=list(groups))
        self.add(shortcut)

        packages = Packages('packages-gitweb', ['gitweb', 'highlight'])
        self.add(packages)

        firewall = Firewall('firewall-gitweb', info.name,
                            ports=['http', 'https'], is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-gitweb', 'gitweb-freedombox',
                              urls=['https://{host}/gitweb/'])
        self.add(webserver)

        self.auth_webserver = GitwebWebserverAuth('webserver-gitweb-auth',
                                                  'gitweb-freedombox-auth')
        self.add(self.auth_webserver)

        users_and_groups = UsersAndGroups('users-and-groups-gitweb',
                                          groups=groups)
        self.add(users_and_groups)

        backup_restore = GitwebBackupRestore('backup-restore-gitweb',
                                             **manifest.backup)
        self.add(backup_restore)

    def post_init(self):
        """Perform post initialization operations."""
        if not self.needs_setup():
            self.update_service_access()

    def set_shortcut_login_required(self, login_required):
        """Change the login_required property of shortcut."""
        shortcut = self.remove('shortcut-gitweb')
        shortcut.login_required = login_required
        self.add(shortcut)

    def update_service_access(self):
        """Update the frontpage shortcut and webserver auth requirement."""
        repos = get_repo_list()
        if have_public_repos(repos):
            self._enable_public_access()
        else:
            self._disable_public_access()

    def _enable_public_access(self):
        """Allow Gitweb app to be accessed by anyone with access."""
        if self.auth_webserver.is_conf_enabled():
            self.auth_webserver.disable()

        self.set_shortcut_login_required(False)

    def _disable_public_access(self):
        """Allow Gitweb app to be accessed by logged-in users only."""
        if not self.auth_webserver.is_conf_enabled():
            self.auth_webserver.enable()

        self.set_shortcut_login_required(True)


class GitwebWebserverAuth(Webserver):
    """Component to handle Gitweb authentication webserver configuration."""

    def is_conf_enabled(self):
        """Check whether Gitweb authentication configuration is enabled."""
        return super().is_enabled()

    def is_enabled(self):
        """Return if configuration is enabled or public access is enabled."""
        repos = get_repo_list()
        return have_public_repos(repos) or super().is_enabled()

    def enable(self):
        """Enable apache configuration only if no public repository exists."""
        repos = get_repo_list()
        if not have_public_repos(repos):
            super().enable()


class GitwebBackupRestore(BackupRestore):
    """Component to handle backup/restore for Gitweb."""

    def restore_post(self, packet):
        """Update access after restoration of backups."""
        app.update_service_access()


def setup(helper, old_version=None):
    """Install and configure the module."""
    app.setup(old_version)
    helper.call('post', actions.superuser_run, 'gitweb', ['setup'])
    helper.call('post', app.enable)


def repo_exists(name):
    """Check whether a remote repository exists."""
    try:
        actions.run('gitweb', ['check-repo-exists', '--url', name])
    except ActionError:
        return False

    return True


def have_public_repos(repos):
    """Check for public repositories"""
    return any((repo['access'] == 'public' for repo in repos))


def create_repo(repo, repo_description, owner, is_private):
    """Create a new repository or clone a remote repository."""
    args = ['--description', repo_description, '--owner', owner]
    if is_private:
        args.append('--is-private')
    if is_repo_url(repo):
        args = ['create-repo', '--url', repo] + args
        # create a repo directory and set correct access rights
        actions.superuser_run('gitweb', args + ['--prepare-only'])
        # start cloning in background
        actions.superuser_run('gitweb', args + ['--skip-prepare'],
                              run_in_background=True)
    else:
        args = ['create-repo', '--name', repo] + args
        actions.superuser_run('gitweb', args)


def get_repo_list():
    """List all git repositories."""
    repos = []
    if os.path.exists(GIT_REPO_PATH):
        for repo in os.listdir(GIT_REPO_PATH):
            if not repo.endswith('.git') or repo.startswith('.'):
                continue

            repo_info = {}
            repo_info['name'] = repo[:-4]

            private_file = os.path.join(GIT_REPO_PATH, repo, 'private')
            if os.path.exists(private_file):
                repo_info['access'] = 'private'
            else:
                repo_info['access'] = 'public'

            progress_file = os.path.join(GIT_REPO_PATH, repo, 'clone_progress')
            if os.path.exists(progress_file):
                with open(progress_file) as file_handle:
                    clone_progress = file_handle.read()
                    repo_info['clone_progress'] = clone_progress

            repos.append(repo_info)

    return sorted(repos, key=lambda repo: repo['name'])


def repo_info(repo):
    """Get information about repository."""
    output = actions.run('gitweb', ['repo-info', '--name', repo])
    info = json.loads(output)
    if info['access'] == 'private':
        info['is_private'] = True
    else:
        info['is_private'] = False
    del info['access']

    return info


def _rename_repo(oldname, newname):
    """Rename a repository."""
    args = ['rename-repo', '--oldname', oldname, '--newname', newname]
    actions.superuser_run('gitweb', args)


def _set_default_branch(repo, branch):
    """Set default branch of the repository."""
    args = [
        'set-default-branch',
        '--name',
        repo,
        '--branch',
        branch,
    ]
    actions.superuser_run('gitweb', args)


def _set_repo_description(repo, repo_description):
    """Set description of the repository."""
    args = [
        'set-repo-description',
        '--name',
        repo,
        '--description',
        repo_description,
    ]
    actions.superuser_run('gitweb', args)


def _set_repo_owner(repo, owner):
    """Set repository's owner name."""
    args = ['set-repo-owner', '--name', repo, '--owner', owner]
    actions.superuser_run('gitweb', args)


def _set_repo_access(repo, access):
    """Set repository's owner name."""
    args = ['set-repo-access', '--name', repo, '--access', access]
    actions.superuser_run('gitweb', args)


def edit_repo(form_initial, form_cleaned):
    """Edit repository data."""
    repo = form_initial['name']

    if form_cleaned['name'] != repo:
        _rename_repo(repo, form_cleaned['name'])
        repo = form_cleaned['name']

    if form_cleaned['description'] != form_initial['description']:
        _set_repo_description(repo, form_cleaned['description'])

    if form_cleaned['owner'] != form_initial['owner']:
        _set_repo_owner(repo, form_cleaned['owner'])

    if form_cleaned['is_private'] != form_initial['is_private']:
        if form_cleaned['is_private']:
            _set_repo_access(repo, 'private')
        else:
            _set_repo_access(repo, 'public')

    if form_cleaned['default_branch'] != form_initial['default_branch']:
        _set_default_branch(repo, form_cleaned['default_branch'])


def delete_repo(repo):
    """Delete a repository."""
    actions.superuser_run('gitweb', ['delete-repo', '--name', repo])
