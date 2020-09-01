# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for gitweb app.
"""

import contextlib
import os
import shutil
import subprocess
import tempfile

from pytest_bdd import given, parsers, scenarios, then, when

from plinth.tests import functional

scenarios('gitweb.feature')

_default_url = functional.config['DEFAULT']['url']


@given('a public repository')
@given('a repository')
@given('at least one repository exists')
def gitweb_repo(session_browser):
    _create_repo(session_browser, 'Test-repo', 'public', True)


@given('a private repository')
def gitweb_private_repo(session_browser):
    _create_repo(session_browser, 'Test-repo', 'private', True)


@given(parsers.parse('a repository with the branch {branch:w}'))
def _create_repo_with_branch(session_browser, branch):
    _delete_repo(session_browser, 'Test-repo', ignore_missing=True)
    _create_repo(session_browser, 'Test-repo', 'public')
    _create_branch('Test-repo', branch)


@given('both public and private repositories exist')
def gitweb_public_and_private_repo(session_browser):
    _create_repo(session_browser, 'Test-repo', 'public', True)
    _create_repo(session_browser, 'Test-repo2', 'private', True)


@given(parsers.parse("a {access:w} repository that doesn't exist"))
def gitweb_nonexistent_repo(session_browser, access):
    _delete_repo(session_browser, 'Test-repo', ignore_missing=True)
    return dict(access=access)


@given('all repositories are private')
def gitweb_all_repositories_private(session_browser):
    _set_all_repos_private(session_browser)


@given(parsers.parse('a repository metadata:\n{metadata}'))
def gitweb_repo_metadata(session_browser, metadata):
    metadata_dict = {}
    for item in metadata.split('\n'):
        item = item.split(': ')
        metadata_dict[item[0]] = item[1]
    return metadata_dict


@when('I create the repository')
def gitweb_create_repo(session_browser, access):
    _create_repo(session_browser, 'Test-repo', access)


@when('I delete the repository')
def gitweb_delete_repo(session_browser):
    _delete_repo(session_browser, 'Test-repo')


@when(parsers.parse('I set {branch:w} as a default branch'))
def gitweb_set_default_branch(session_browser, branch):
    _set_default_branch(session_browser, 'Test-repo', branch)


@when('I set the metadata of the repository')
def gitweb_edit_repo_metadata(session_browser, gitweb_repo_metadata):
    _edit_repo_metadata(session_browser, 'Test-repo', gitweb_repo_metadata)


@when('using a git client')
def gitweb_using_git_client():
    pass


@then(
    parsers.parse(
        'the gitweb site should show {branch:w} as a default repo branch'))
def gitweb_site_check_default_repo_branch(session_browser, branch):
    assert _get_gitweb_site_default_repo_branch(session_browser,
                                                'Test-repo') == branch


@then('the repository should be restored')
@then('the repository should be listed as a public')
def gitweb_repo_should_exists(session_browser):
    assert _repo_exists(session_browser, 'Test-repo', access='public')


@then('the repository should be listed as a private')
def gitweb_private_repo_should_exists(session_browser):
    assert _repo_exists(session_browser, 'Test-repo', 'private')


@then('the repository should not be listed')
def gitweb_repo_should_not_exist(session_browser, gitweb_repo):
    assert not _repo_exists(session_browser, gitweb_repo)


@then('the public repository should be listed on gitweb')
@then('the repository should be listed on gitweb')
def gitweb_repo_should_exist_on_gitweb(session_browser):
    assert _site_repo_exists(session_browser, 'Test-repo')


@then('the private repository should not be listed on gitweb')
def gitweb_private_repo_should_exists_on_gitweb(session_browser):
    assert not _site_repo_exists(session_browser, 'Test-repo2')


@then('the metadata of the repository should be as set')
def gitweb_repo_metadata_should_match(session_browser, gitweb_repo_metadata):
    actual_metadata = _get_repo_metadata(session_browser, 'Test-repo')
    assert all(item in actual_metadata.items()
               for item in gitweb_repo_metadata.items())


@then('the repository should be publicly readable')
def gitweb_repo_publicly_readable():
    assert _repo_is_readable('Test-repo')
    assert _repo_is_readable('Test-repo', url_git_extension=True)


@then('the repository should not be publicly readable')
def gitweb_repo_not_publicly_readable():
    assert not _repo_is_readable('Test-repo')
    assert not _repo_is_readable('Test-repo', url_git_extension=True)


@then('the repository should not be publicly writable')
def gitweb_repo_not_publicly_writable():
    assert not _repo_is_writable('Test-repo')
    assert not _repo_is_writable('Test-repo', url_git_extension=True)


@then('the repository should be privately readable')
def gitweb_repo_privately_readable():
    assert _repo_is_readable('Test-repo', with_auth=True)
    assert _repo_is_readable('Test-repo', with_auth=True,
                             url_git_extension=True)


@then('the repository should be privately writable')
def gitweb_repo_privately_writable():
    assert _repo_is_writable('Test-repo', with_auth=True)
    assert _repo_is_writable('Test-repo', with_auth=True,
                             url_git_extension=True)


def _create_branch(repo, branch):
    """Create a branch on the remote repository."""
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
        browser.find_link_by_href('/plinth/apps/gitweb/create/').first.click()
        browser.find_by_id('id_gitweb-name').fill(repo)
        if access == 'private':
            browser.find_by_id('id_gitweb-is_private').check()
        elif access == 'public':
            browser.find_by_id('id_gitweb-is_private').uncheck()
        functional.submit(browser)
    elif not ok_if_exists:
        assert False, 'Repo already exists.'


def _delete_repo(browser, repo, ignore_missing=False):
    """Delete repository."""
    functional.nav_to_module(browser, 'gitweb')
    delete_link = browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/delete/'.format(repo))
    if delete_link or not ignore_missing:
        delete_link.first.click()
        functional.submit(browser)


def _edit_repo_metadata(browser, repo, metadata):
    """Set repository metadata."""
    functional.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    if 'name' in metadata:
        browser.find_by_id('id_gitweb-name').fill(metadata['name'])
    if 'description' in metadata:
        browser.find_by_id('id_gitweb-description').fill(
            metadata['description'])
    if 'owner' in metadata:
        browser.find_by_id('id_gitweb-owner').fill(metadata['owner'])
    if 'access' in metadata:
        if metadata['access'] == 'private':
            browser.find_by_id('id_gitweb-is_private').check()
        else:
            browser.find_by_id('id_gitweb-is_private').uncheck()
    functional.submit(browser)


def _get_gitweb_site_default_repo_branch(browser, repo):
    functional.nav_to_module(browser, 'gitweb')
    browser.find_by_css('a[href="/gitweb/{0}.git"]'.format(repo)).first.click()

    return browser.find_by_css('.head').first.text


def _get_repo_metadata(browser, repo):
    """Get repository metadata."""
    functional.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
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


@contextlib.contextmanager
def _gitweb_temp_directory():
    """Create temporary directory"""
    name = tempfile.mkdtemp(prefix='plinth_test_gitweb_')
    yield name
    shutil.rmtree(name)


def _gitweb_git_command_is_successful(command, cwd):
    """Check if a command runs successfully or gives authentication error"""
    process = subprocess.run(command, capture_output=True, cwd=cwd)
    if process.returncode != 0:
        if 'Authentication failed' in process.stderr.decode():
            return False
        print(process.stdout.decode())
        # raise exception
        process.check_returncode()
    return True


def _repo_exists(browser, repo, access=None):
    """Check whether the repository exists."""
    functional.nav_to_module(browser, 'gitweb')
    links_found = browser.find_link_by_href('/gitweb/{}.git'.format(repo))
    access_matches = True
    if links_found and access:
        parent = links_found.first.find_by_xpath('..').first
        private_icon = parent.find_by_css('.repo-private-icon')
        if access == 'private':
            access_matches = bool(private_icon)
        if access == 'public':
            access_matches = not bool(private_icon)
    return bool(links_found) and access_matches


def _repo_is_readable(repo, with_auth=False, url_git_extension=False):
    """Check if a git repo is readable with git client."""
    url = _get_repo_url(repo, with_auth)
    if url_git_extension:
        url = url + '.git'
    git_command = ['git', 'clone', '-c', 'http.sslverify=false', url]
    with _gitweb_temp_directory() as cwd:
        return _gitweb_git_command_is_successful(git_command, cwd)


def _repo_is_writable(repo, with_auth=False, url_git_extension=False):
    """Check if a git repo is writable with git client."""
    url = _get_repo_url(repo, with_auth)
    if url_git_extension:
        url = url + '.git'

    with _gitweb_temp_directory() as temp_directory:
        repo_directory = os.path.join(temp_directory, 'test-project')
        _create_local_repo(repo_directory)

        git_push_command = ['git', 'push', '-qf', url, 'master']

        return _gitweb_git_command_is_successful(git_push_command,
                                                 repo_directory)


def _set_default_branch(browser, repo, branch):
    """Set default branch of the repository."""
    functional.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    browser.find_by_id('id_gitweb-default_branch').select(branch)
    functional.submit(browser)


def _set_repo_access(browser, repo, access):
    """Set repository as public or private."""
    functional.nav_to_module(browser, 'gitweb')
    browser.find_link_by_href(
        '/plinth/apps/gitweb/{}/edit/'.format(repo)).first.click()
    if access == 'private':
        browser.find_by_id('id_gitweb-is_private').check()
    else:
        browser.find_by_id('id_gitweb-is_private').uncheck()
    functional.submit(browser)


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


def _site_repo_exists(browser, repo):
    """Check whether the repository exists on Gitweb site."""
    browser.visit('{}/gitweb'.format(_default_url))
    return browser.find_by_css('a[href="/gitweb/{0}.git"]'.format(repo))
