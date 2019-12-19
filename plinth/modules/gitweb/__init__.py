#
# This file is part of FreedomBox.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
FreedomBox app to configure Gitweb.
"""

import json
import os

from django.utils.translation import ugettext_lazy as _

from plinth import action_utils, actions
from plinth import app as app_module
from plinth import frontpage, menu
from plinth.errors import ActionError
from plinth.modules.apache.components import Webserver
from plinth.modules.firewall.components import Firewall
from plinth.modules.users import register_group

from .forms import is_repo_url
from .manifest import GIT_REPO_PATH, backup, clients  # noqa, pylint: disable=unused-import

clients = clients

version = 1

managed_packages = ['gitweb', 'highlight']

name = _('Gitweb')

icon_filename = 'gitweb'

short_description = _('Simple Git Hosting')

description = [
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

group = ('git-access', _('Read-write access to Git repositories'))

app = None


class GitwebApp(app_module.App):
    """FreedomBox app for Gitweb."""

    app_id = 'gitweb'

    def __init__(self):
        """Create components for the app."""
        super().__init__()

        self.repos = []

        menu_item = menu.Menu('menu-gitweb', name, short_description, 'gitweb',
                              'gitweb:index', parent_url_name='apps')
        self.add(menu_item)

        shortcut = frontpage.Shortcut('shortcut-gitweb', name,
                                      short_description=short_description,
                                      icon=icon_filename, url='/gitweb/',
                                      clients=clients, login_required=True,
                                      allowed_groups=[group[0]])
        self.add(shortcut)

        firewall = Firewall('firewall-gitweb', name, ports=['http', 'https'],
                            is_external=True)
        self.add(firewall)

        webserver = Webserver('webserver-gitweb', 'gitweb-freedombox')
        self.add(webserver)

        self.auth_webserver = GitwebWebserverAuth('webserver-gitweb-auth',
                                                  'gitweb-freedombox-auth')
        self.add(self.auth_webserver)

    def set_shortcut_login_required(self, login_required):
        """Change the login_required property of shortcut."""
        shortcut = self.remove('shortcut-gitweb')
        shortcut.login_required = login_required
        self.add(shortcut)

    def get_repo_list(self):
        """List all Git repositories and set Gitweb as public or private."""
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

                progress_file = os.path.join(GIT_REPO_PATH, repo,
                                             'clone_progress')
                if os.path.exists(progress_file):
                    with open(progress_file) as file_handle:
                        clone_progress = file_handle.read()
                        repo_info['clone_progress'] = clone_progress

                repos.append(repo_info)

        return sorted(repos, key=lambda repo: repo['name'])

    def update_service_access(self):
        """Update the frontpage shortcut and webserver auth requirement."""
        repos = self.get_repo_list()
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
        repos = app.get_repo_list()
        return have_public_repos(repos) or super().is_enabled()

    def enable(self):
        """Enable apache configuration only if no public repository exists."""
        repos = app.get_repo_list()
        if not have_public_repos(repos):
            super().enable()


def init():
    """Initialize the module."""
    global app
    app = GitwebApp()
    register_group(group)

    setup_helper = globals()['setup_helper']
    if setup_helper.get_state() != 'needs-setup':
        app.update_service_access()
        if app.is_enabled():
            app.set_enabled(True)


def setup(helper, old_version=None):
    """Install and configure the module."""
    helper.install(managed_packages)
    helper.call('post', actions.superuser_run, 'gitweb', ['setup'])
    helper.call('post', app.enable)


def diagnose():
    """Run diagnostics and return the results."""
    results = []

    results.extend(
        action_utils.diagnose_url_on_all('https://{host}/gitweb/',
                                         check_certificate=False))
    return results


def restore_post(packet):
    """Update access after restoration of backups."""
    app.update_service_access()


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


def repo_info(repo):
    """Get information about repository."""
    output = actions.run('gitweb', ['repo-info', '--name', repo])
    info = json.loads(output)
    if info['access'] == 'private':
        info['is_private'] = True
    else:
        info['is_private'] = False

    return info


def _rename_repo(oldname, newname):
    """Rename a repository."""
    args = ['rename-repo', '--oldname', oldname, '--newname', newname]
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


def delete_repo(repo):
    """Delete a repository."""
    actions.superuser_run('gitweb', ['delete-repo', '--name', repo])
