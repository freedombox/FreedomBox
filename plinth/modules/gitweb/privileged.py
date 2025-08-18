# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configuration helper for Gitweb."""

import configparser
import logging
import os
import re
import shutil
import subprocess
import time
from typing import Any

from plinth import action_utils
from plinth.actions import privileged
from plinth.modules.gitweb.forms import RepositoryValidator, get_name_from_url
from plinth.modules.gitweb.manifest import GIT_REPO_PATH, REPO_DIR_OWNER

logger = logging.getLogger(__name__)


def validate_repo_name(name: str) -> str:
    """Validate a repository name and add .git extension if necessary."""
    RepositoryValidator()(name)
    if not name.endswith('.git'):
        name = name + '.git'

    return name


def validate_repo_url(url: str) -> str:
    """Validate a repository URL."""
    RepositoryValidator(input_should_be='url')(url)
    return url


@privileged
def setup():
    """Disable default Apache2 Gitweb configuration."""
    action_utils.webserver_disable('gitweb')
    if not _get_global_default_branch():
        _set_global_default_branch('main')


def _get_global_default_branch():
    """Get globally configured default branch name."""
    try:
        default_branch = action_utils.run(
            ['git', 'config', '--global', '--get', 'init.defaultBranch'],
            check=True).stdout.decode().strip()
    except subprocess.CalledProcessError as exception:
        if exception.returncode == 1:  # Default branch not configured
            return None
        raise

    return default_branch


def _set_global_default_branch(name):
    """Configure default branch name globally."""
    action_utils.run(['git', 'config', '--global', 'init.defaultBranch', name],
                     check=True)


def _clone_with_progress_report(url, repo_dir):
    """Clone a repository and write progress info to the file."""
    starttime = time.time()
    status_file = repo_dir / 'clone_progress'
    repo_temp_dir = repo_dir / '.temp'
    # do not ask for credidentials and set low speed timeout
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', LC_ALL='C',
               GIT_HTTP_LOW_SPEED_LIMIT='100', GIT_HTTP_LOW_SPEED_TIME='60')

    proc = subprocess.Popen(
        ['git', 'clone', '--bare', '--progress', url,
         str(repo_temp_dir)], stderr=subprocess.PIPE, text=True, env=env)

    # write clone progress to the file
    errors = []
    while True:
        line = proc.stderr.readline()
        if not line:
            break

        if 'error:' in line or 'fatal:' in line:
            errors.append(line.strip())

        currenttime = time.time()
        if currenttime - starttime > 1:
            elapsed = _clone_status_line_to_percent(line)
            if elapsed is not None:
                try:
                    status_file.write_text(elapsed)
                except OSError as error:
                    errors.append(str(error))

            starttime = currenttime

    # make sure process is ended
    try:
        proc.communicate(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()

    status_file.unlink()
    if proc.returncode != 0:
        shutil.rmtree(repo_dir)
        logger.error('Git repository cloning failed: %s', '\n'.join(errors))
        raise RuntimeError('Git repository cloning failed.', errors)


def _prepare_clone_repo(url: str, is_private: bool):
    """Prepare cloning a repository."""
    repo_name = get_name_from_url(url)
    if not repo_name.endswith('.git'):
        repo_name = repo_name + '.git'

    repo_dir = GIT_REPO_PATH / repo_name
    os.mkdir(repo_dir)

    status_file = repo_dir / 'clone_progress'
    try:
        if is_private:
            _set_access_status(repo_name, 'private')

        status_file.write_text('0')
    except OSError:
        shutil.rmtree(repo_dir)
        raise


def _clone_status_line_to_percent(line):
    """Parse Git clone command output."""
    result = re.match(r'.* ([0-9]+)% ', line)
    if result is not None:
        text = result.group(0)
        progress = int(result.group(1))
        if 'Counting objects' in text:
            total_progress = 0.05 * progress
        elif 'Compressing objects' in text:
            total_progress = 5 + 0.05 * progress
        elif 'Receiving objects' in text:
            total_progress = 10 + 0.6 * progress
        elif 'Resolving deltas' in text:
            total_progress = 70 + 0.3 * progress
        else:
            return None

        return str(int(total_progress))

    return None


def _clone_repo(url: str, description: str, owner: str, keep_ownership: bool):
    """Clone a repository."""
    repo = get_name_from_url(url)
    if not repo.endswith('.git'):
        repo = repo + '.git'

    repo_path = GIT_REPO_PATH / repo
    repo_temp_path = repo_path / '.temp'

    _clone_with_progress_report(url, repo_path)

    for item in os.listdir(repo_temp_path):
        shutil.move(os.path.join(repo_temp_path, item), repo_path)

    shutil.rmtree(repo_temp_path)
    if not keep_ownership:
        action_utils.run(
            ['chown', '-R', f'{REPO_DIR_OWNER}:{REPO_DIR_OWNER}', repo],
            cwd=GIT_REPO_PATH, check=True)

    _set_repo_description(repo, description)
    _set_repo_owner(repo, owner)


def _create_repo(repo: str, description: str, owner: str, is_private: bool,
                 keep_ownership: bool):
    """Create an empty repository."""
    try:
        action_utils.run(['git', 'init', '-q', '--bare', repo],
                         cwd=GIT_REPO_PATH, check=True)
        if not keep_ownership:
            action_utils.run(
                ['chown', '-R', f'{REPO_DIR_OWNER}:{REPO_DIR_OWNER}', repo],
                cwd=GIT_REPO_PATH, check=True)
        _set_repo_description(repo, description)
        _set_repo_owner(repo, owner)
        if is_private:
            _set_access_status(repo, 'private')
    except (subprocess.CalledProcessError, OSError):
        repo_path = GIT_REPO_PATH / repo
        if repo_path.is_dir():
            shutil.rmtree(repo_path)
        raise


def _get_default_branch(repo):
    """Get default branch of the repository."""
    repo_path = GIT_REPO_PATH / repo

    return action_utils.run_as_user(
        ['git', '-C',
         str(repo_path), 'symbolic-ref', '--short', 'HEAD'],
        username=REPO_DIR_OWNER, check=True,
        stdout=subprocess.PIPE).stdout.decode().strip()


def _get_repo_description(repo):
    """Set description of the repository."""
    description_file = GIT_REPO_PATH / repo / 'description'
    if description_file.exists():
        description = description_file.read_text()
    else:
        description = ''

    return description


def _set_repo_description(repo, description):
    """Set description of the repository."""
    description_file = GIT_REPO_PATH / repo / 'description'
    description_file.write_text(description)


def _get_repo_owner(repo):
    """Set repository's owner name."""
    repo_config = GIT_REPO_PATH / repo / 'config'
    config = configparser.ConfigParser()
    config.read(repo_config)
    try:
        owner = config['gitweb']['owner']
    except KeyError:
        owner = ''

    return owner


def _set_repo_owner(repo, owner):
    """Set repository's owner name."""
    repo_config = GIT_REPO_PATH / repo / 'config'
    config = configparser.ConfigParser()
    config.read(repo_config)
    if not config.has_section('gitweb'):
        config.add_section('gitweb')

    config['gitweb']['owner'] = owner
    with repo_config.open('w', encoding='utf-8') as file_handle:
        config.write(file_handle)


def _get_access_status(repo):
    """Get repository's access status."""
    private_file = GIT_REPO_PATH / repo / 'private'
    if private_file.exists():
        return 'private'

    return 'public'


def _set_access_status(repo, status):
    """Set repository as private or public."""
    private_file = GIT_REPO_PATH / repo / 'private'
    if status == 'private':
        private_file.touch()
    elif status == 'public':
        private_file.unlink(missing_ok=True)


def _get_branches(repo):
    """Return list of the branches in the repository."""
    process = action_utils.run_as_user(
        ['git', '-C', repo, 'branch', '--format=%(refname:short)'],
        cwd=GIT_REPO_PATH, username=REPO_DIR_OWNER, check=True,
        stdout=subprocess.PIPE)

    return process.stdout.decode().strip().split()


@privileged
def get_branches(name: str) -> dict[str, Any]:
    """Check whether a branch exists in the repository."""
    repo = validate_repo_name(name)
    return dict(default_branch=_get_default_branch(repo),
                branches=_get_branches(repo))


@privileged
def rename_repo(old_name: str, new_name: str):
    """Rename a repository."""
    old_name = validate_repo_name(old_name)
    new_name = validate_repo_name(new_name)
    oldpath = GIT_REPO_PATH / old_name
    newpath = GIT_REPO_PATH / new_name
    oldpath.rename(newpath)


@privileged
def set_default_branch(name: str, branch: str):
    """Set description of the repository."""
    repo = validate_repo_name(name)
    if branch not in _get_branches(repo):
        raise ValueError('No such branch')

    action_utils.run_as_user(
        ['git', '-C', repo, 'symbolic-ref', 'HEAD', f'refs/heads/{branch}'],
        cwd=GIT_REPO_PATH, check=True, username=REPO_DIR_OWNER)


@privileged
def set_repo_description(name: str, description: str):
    """Set description of the repository."""
    repo = validate_repo_name(name)
    _set_repo_description(repo, description)


@privileged
def set_repo_owner(name: str, owner: str):
    """Set repository's owner name."""
    repo = validate_repo_name(name)
    _set_repo_owner(repo, owner)


@privileged
def set_repo_access(name: str, access: str):
    """Set repository's access status."""
    repo = validate_repo_name(name)
    if access not in ('public', 'private'):
        raise ValueError('Invalid access parameter')

    _set_access_status(repo, access)


@privileged
def repo_info(name: str) -> dict[str, str]:
    """Get information about repository."""
    repo = validate_repo_name(name)
    repo_path = GIT_REPO_PATH / repo
    if not repo_path.exists():
        raise RuntimeError('Repository not found')

    return dict(name=repo[:-4], description=_get_repo_description(repo),
                owner=_get_repo_owner(repo), access=_get_access_status(repo),
                default_branch=_get_default_branch(repo))


@privileged
def create_repo(url: str | None = None, name: str | None = None,
                description: str = '', owner: str = '',
                keep_ownership: bool = False, is_private: bool = False,
                skip_prepare: bool = False, prepare_only: bool = False):
    """Create a new or clone a remote repository."""
    if url:
        url = validate_repo_url(url)

    if name:
        repo = validate_repo_name(name)

    if url:
        if not skip_prepare:
            _prepare_clone_repo(url, is_private)

        if not prepare_only:
            _clone_repo(url, description, owner, keep_ownership)
    elif repo is not None:
        _create_repo(repo, description, owner, is_private, keep_ownership)


@privileged
def repo_exists(url: str) -> bool:
    """Return whether remote repository exists."""
    url = validate_repo_url(url)
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
    try:
        action_utils.run(['git', 'ls-remote', url, 'HEAD'], timeout=10,
                         env=env, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


@privileged
def delete_repo(name: str):
    """Delete a git repository."""
    repo = validate_repo_name(name)
    repo_path = GIT_REPO_PATH / repo
    shutil.rmtree(repo_path)


@privileged
def uninstall():
    """Remove git repositories."""
    for item in GIT_REPO_PATH.iterdir():
        shutil.rmtree(item, ignore_errors=True)
