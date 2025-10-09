# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure ikiwiki."""

import os
import pathlib
import re
import shutil

from plinth import action_utils
from plinth.actions import privileged, secret_str

SETUP_WIKI = '/etc/ikiwiki/plinth-wiki.setup'
SETUP_BLOG = '/etc/ikiwiki/plinth-blog.setup'
SITE_PATH = '/var/www/ikiwiki'
WIKI_PATH = '/var/lib/ikiwiki'


def _is_safe_path(basedir, path):
    """Return whether a path is safe."""
    return os.path.realpath(path).startswith(basedir)


@privileged
def setup():
    """Write Apache configuration and wiki/blog setup scripts."""
    if not os.path.exists(SITE_PATH):
        os.makedirs(SITE_PATH)


def _get_title(site):
    """Get blog or wiki title."""
    try:
        with open(os.path.join(SITE_PATH, site, 'index.html'),
                  encoding='utf-8') as index_file:
            match = re.search(r'<title>(.*)</title>', index_file.read())
            if match:
                return match[1]
    except FileNotFoundError:
        pass

    return site


@privileged
def get_sites() -> list[tuple[str, str]]:
    """Get wikis and blogs."""
    sites = []
    if os.path.exists(SITE_PATH):
        for site in os.listdir(SITE_PATH):
            if not os.path.isdir(os.path.join(SITE_PATH, site)):
                continue

            title = _get_title(site)
            sites.append((site, title))

    return sites


@privileged
def create_wiki(wiki_name: str, admin_name: str, admin_password: secret_str):
    """Create a wiki."""
    pw_bytes = admin_password.encode()
    input_ = pw_bytes + b'\n' + pw_bytes
    action_utils.run(['ikiwiki', '-setup', SETUP_WIKI, wiki_name, admin_name],
                     input=input_, env=dict(os.environ,
                                            PERL_UNICODE='AS'), check=True)


@privileged
def create_blog(blog_name: str, admin_name: str, admin_password: secret_str):
    """Create a blog."""
    pw_bytes = admin_password.encode()
    input_ = pw_bytes + b'\n' + pw_bytes
    action_utils.run(['ikiwiki', '-setup', SETUP_BLOG, blog_name, admin_name],
                     input=input_, env=dict(os.environ, PERL_UNICODE='AS'))


@privileged
def setup_site(site_name: str):
    """Run setup for a site."""
    setup_path = os.path.join(WIKI_PATH, site_name + '.setup')
    action_utils.run(['ikiwiki', '-setup', setup_path], check=True)


@privileged
def delete(name: str):
    """Delete a wiki or blog."""
    html_folder = os.path.join(SITE_PATH, name)
    wiki_folder = os.path.join(WIKI_PATH, name)

    if not (_is_safe_path(SITE_PATH, html_folder)
            and _is_safe_path(WIKI_PATH, wiki_folder)):
        raise ValueError(
            'Error: {0} is not a correct wiki/blog name.'.format(name))

    shutil.rmtree(html_folder, ignore_errors=True)
    shutil.rmtree(wiki_folder, ignore_errors=True)
    shutil.rmtree(wiki_folder + '.git', ignore_errors=True)
    pathlib.Path(wiki_folder + '.setup').unlink(missing_ok=True)


@privileged
def uninstall():
    """Remove all ikiwiki sites."""
    for site in get_sites():
        delete(site[0])
