# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for gitweb app.
"""
import contextlib
import os
import shutil
import subprocess
import tempfile

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.gitweb]

_default_url = functional.config['DEFAULT']['url']


class TestGitwebApp(functional.BaseAppTests):
    app_name = 'gitweb'
    has_service = False
    has_web = True

    def test_all_repos_private(self, session_browser):
        """Test repo accessability when all repos are private."""
        _create_repo(session_browser, 'Test-repo', 'private',
                     ok_if_exists=True)
        _set_all_repos_private(session_browser)
        if not functional.user_exists(session_browser, 'gitweb_user'):
            functional.create_user(session_browser, 'gitweb_user',
                                   groups=['git-access'])
        if not functional.user_exists(session_browser, 'nogroupuser'):
            functional.create_user(session_browser, 'nogroupuser', groups=[])

        functional.login_with_account(session_browser, functional.base_url,
                                      'gitweb_user')
        assert functional.is_available(session_browser, 'gitweb')
        assert len(functional.find_on_front_page(session_browser,
                                                 'gitweb')) == 1

        functional.login_with_account(session_browser, functional.base_url,
                                      'nogroupuser')
        assert not functional.is_available(session_browser, 'gitweb')
        assert len(functional.find_on_front_page(session_browser,
                                                 'gitweb')) == 0

        functional.logout(session_browser)
        functional.access_url(session_browser, 'gitweb')
        assert functional.is_login_prompt(session_browser)
        assert len(functional.find_on_front_page(session_browser,
                                                 'gitweb')) == 0

    @pytest.mark.backups
    def test_backup_restore(self, session_browser):
        """Test backing up and restoring."""
        _create_repo(session_browser, 'Test-repo', ok_if_exists=True)
        functional.backup_create(session_browser, 'gitweb', 'test_gitweb')
        _delete_repo(session_browser, 'Test-repo')
        functional.backup_restore(session_browser, 'gitweb', 'test_gitweb')
        assert _repo_exists(session_browser, 'Test-repo')
        assert functional.is_available(session_browser, 'gitweb')

    @pytest.mark.parametrize('access', ['public', 'private'])
    @pytest.mark.parametrize('repo_name', ['Test-repo', 'Test-repo.git'])
    def test_create_delete_repo(self, session_browser, access, repo_name):
        """Test creating and deleting a repo and accessing with a git
        client."""
        _delete_repo(session_browser, repo_name, ignore_missing=True)
        _create_repo(session_browser, repo_name, access)

        assert _repo_exists(session_browser, repo_name, access)
        assert _site_repo_exists(session_browser, repo_name)

        if access == "public":
            assert _repo_is_readable(repo_name)
        else:
            assert not _repo_is_readable(repo_name)

        assert not _repo_is_writable(repo_name)
        assert _repo_is_readable(repo_name, with_auth=True)
        assert _repo_is_writable(repo_name, with_auth=True)

        _delete_repo(session_browser, repo_name)
        assert not _repo_exists(session_browser, repo_name)

    def test_both_private_and_public_repo_exist(self, session_browser):
        """Tests when both private and public repo exist."""
        _create_repo(session_browser, 'Test-repo', 'public', True)
        _create_repo(session_browser, 'Test-repo-private', 'private', True)

        functional.logout(session_browser)
        assert _site_repo_exists(session_browser, 'Test-repo')
        assert not _site_repo_exists(session_browser, 'Test-repo-private')

    def test_edit_repo_metadata(self, session_browser):
        """Test edit repo metadata."""
        _create_repo(session_browser, 'Test-repo2', 'public',
                     ok_if_exists=True)
        _delete_repo(session_browser, 'Test-repo', ignore_missing=True)
        repo_metadata = {
            'name': 'Test-repo',
            'description': 'Test Description',
            'owner': 'Test Owner',
            'access': 'private',
        }
        _edit_repo_metadata(session_browser, 'Test-repo2', repo_metadata)
        assert _get_repo_metadata(session_browser,
                                  "Test-repo") == repo_metadata

        _create_branch('Test-repo', 'branch1')
        _set_default_branch(session_browser, 'Test-repo', 'branch1')
        assert _get_gitweb_site_default_repo_branch(session_browser,
                                                    'Test-repo') == 'branch1'


def _create_local_repo(path):
    """Create a local repository."""
    shutil.rmtree(path, ignore_errors=True)
    os.mkdir(path)
    create_repo_commands = [
        'git init -q', 'git config http.sslVerify false',
        'git -c "user.name=Tester" -c "user.email=tester" '
        'commit -q --allow-empty -m "test"'
    ]
    for command in create_repo_commands:
        subprocess.check_call(command, shell=True, cwd=path)


def _create_repo(browser, repo, access=None, ok_if_exists=False):
    """Create repository."""
    if not _repo_exists(browser, repo, access):
        _delete_repo(browser, repo, ignore_missing=True)
        browser.links.find_by_href('/plinth/apps/gitweb/create/').first.click()
        browser.find_by_id('id_gitweb-name').fill(repo)
        if access == 'private':
            browser.find_by_id('id_gitweb-is_private').check()
        elif access == 'public':
            browser.find_by_id('id_gitweb-is_private').uncheck()
        functional.submit(browser, form_class='form-gitweb')
    elif not ok_if_exists:
        assert False, 'Repo already exists.'


def _create_branch(repo, branch):
    """Add a branch to the repo."""
    repo_url = _get_repo_url(repo, with_auth=True)

    with _gitweb_temp_directory() as temp_directory:
        repo_path = os.path.join(temp_directory, repo)

        _create_local_repo(repo_path)

        add_branch_commands = [['git', 'checkout', '-q', '-b', branch],
                               [
                                   'git', '-c', 'user.name=Tester', '-c',
                                   'user.email=tester', 'commit', '-q',
                                   '--allow-empty', '-m', 'test_branch1'
                               ],
                               ['git', 'push', '-q', '-f', repo_url, branch]]
        for command in add_branch_commands:
            subprocess.check_call(command, cwd=repo_path)


def _delete_repo(browser, repo, ignore_missing=False):
    """Delete repository."""
    functional.nav_to_module(browser, 'gitweb')
    if repo.endswith('.git'):
        repo = repo[:-4]
    delete_link = browser.links.find_by_href(
        '/plinth/apps/gitweb/{}/delete/'.format(repo))
    if delete_link or not ignore_missing:
        delete_link.first.click()
        functional.submit(browser, form_class='form-delete')


def _edit_repo_metadata(browser, repo, metadata):
    """Set repository metadata."""
    functional.nav_to_module(browser, 'gitweb')
    browser.links.find_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    browser.find_by_id('id_gitweb-name').fill(metadata['name'])
    browser.find_by_id('id_gitweb-description').fill(metadata['description'])
    browser.find_by_id('id_gitweb-owner').fill(metadata['owner'])
    if metadata['access'] == 'private':
        browser.find_by_id('id_gitweb-is_private').check()
    else:
        browser.find_by_id('id_gitweb-is_private').uncheck()
    functional.submit(browser, form_class='form-gitweb')


def _get_gitweb_site_default_repo_branch(browser, repo):
    functional.nav_to_module(browser, 'gitweb')
    browser.find_by_css('a[href="/gitweb/{0}.git"]'.format(repo)).first.click()

    return browser.find_by_css('.head').first.text


def _get_repo_metadata(browser, repo):
    """Get repository metadata."""
    functional.nav_to_module(browser, 'gitweb')
    browser.links.find_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    metadata = {}
    for item in ['name', 'description', 'owner']:
        metadata[item] = browser.find_by_id('id_gitweb-' + item).value
    if browser.find_by_id('id_gitweb-is_private').value:
        metadata['access'] = 'private'
    else:
        metadata['access'] = 'public'
    return metadata


def _get_repo_url(repo, with_auth):
    """"Get repository URL"""
    scheme = 'http'
    if _default_url.startswith('https://'):
        scheme = 'https'
    url = _default_url.split(
        '://')[1] if '://' in _default_url else _default_url
    password = 'gitweb_wrong_password'
    if with_auth:
        password = functional.config['DEFAULT']['password']

    return '{0}://{1}:{2}@{3}/gitweb/{4}'.format(
        scheme, functional.config['DEFAULT']['username'], password, url, repo)


def _gitweb_git_command_is_successful(command, cwd):
    """Check if a command runs successfully or gives authentication error"""
    # Tell OS not to translate command return messages
    env = os.environ.copy()
    env['LC_ALL'] = 'C'

    process = subprocess.run(command, capture_output=True, cwd=cwd, env=env,
                             check=False)
    if process.returncode != 0:
        if 'Authentication failed' in process.stderr.decode():
            return False

        process.check_returncode()  # Raise exception
    return True


@contextlib.contextmanager
def _gitweb_temp_directory():
    """Create temporary directory"""
    name = tempfile.mkdtemp(prefix='plinth_test_gitweb_')
    yield name
    shutil.rmtree(name)


def _repo_exists(browser, repo, access=None):
    """Check whether the repository exists."""
    functional.nav_to_module(browser, 'gitweb')
    if not repo.endswith('.git'):
        repo = repo + ".git"
    links_found = browser.links.find_by_href('/gitweb/{}'.format(repo))
    access_matches = True
    if links_found and access:
        parent = links_found.first.find_by_xpath('..').first
        private_icon = parent.find_by_css('.repo-private-icon')
        if access == 'private':
            access_matches = bool(private_icon)
        if access == 'public':
            access_matches = not bool(private_icon)
    return bool(links_found) and access_matches


def _repo_is_readable(repo, with_auth=False):
    """Check if a git repo is readable with git client."""
    url = _get_repo_url(repo, with_auth)
    git_command = ['git', 'clone', '-c', 'http.sslverify=false', url]
    with _gitweb_temp_directory() as cwd:
        return _gitweb_git_command_is_successful(git_command, cwd)


def _repo_is_writable(repo, with_auth=False):
    """Check if a git repo is writable with git client."""
    url = _get_repo_url(repo, with_auth)
    with _gitweb_temp_directory() as temp_directory:
        repo_directory = os.path.join(temp_directory, 'test-project')
        _create_local_repo(repo_directory)
        git_push_command = [
            'git', '-c', 'push.default=current', 'push', '-qf', url
        ]
        return _gitweb_git_command_is_successful(git_push_command,
                                                 repo_directory)


def _set_all_repos_private(browser):
    """Set all repositories private"""
    functional.nav_to_module(browser, 'gitweb')
    public_repos = []
    for element in browser.find_by_css('#gitweb-repo-list .list-group-item'):
        if not element.find_by_css('.repo-private-icon'):
            repo = element.find_by_css('.repo-label').first.text
            public_repos.append(repo)
    for repo in public_repos:
        _set_repo_access(browser, repo, 'private')


def _set_default_branch(browser, repo, branch):
    """Set default branch of the repository."""
    functional.nav_to_module(browser, 'gitweb')
    browser.links.find_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    browser.find_by_id('id_gitweb-default_branch').select(branch)
    functional.submit(browser, form_class='form-gitweb')


def _set_repo_access(browser, repo, access):
    """Set repository as public or private."""
    functional.nav_to_module(browser, 'gitweb')
    browser.links.find_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    if access == 'private':
        browser.find_by_id('id_gitweb-is_private').check()
    else:
        browser.find_by_id('id_gitweb-is_private').uncheck()
    functional.submit(browser, form_class='form-gitweb')


def _site_repo_exists(browser, repo):
    """Check whether the repository exists on Gitweb site."""
    browser.visit('{}/gitweb'.format(_default_url))
    if not repo.endswith('.git'):
        repo = repo + ".git"
    return bool(browser.find_by_css('a[href="/gitweb/{0}"]'.format(repo)))
