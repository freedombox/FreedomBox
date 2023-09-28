#!/usr/bin/python3
# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox Service setup file.

isort:skip_file
"""

import collections
import glob
import os
import pathlib
import re
import shutil
import subprocess
import setuptools
from setuptools.command.install import install

from distutils import log
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.core import Command
from distutils.dir_util import remove_tree
from distutils.util import change_root

from plinth import __version__

DIRECTORIES_TO_CREATE = [
    '/var/lib/plinth',
    '/var/lib/plinth/sessions',
]

DIRECTORIES_TO_COPY = [
    ('/usr/share/plinth/static', 'static'),
]

ENABLED_APPS_PATH = "/usr/share/freedombox/modules-enabled/"

DISABLED_APPS_TO_REMOVE = [
    'apps',
    'coquelicot',
    'diaspora',
    'monkeysphere',
    'owncloud',
    'system',
    'xmpp',
    'disks',
    'udiskie',
    'restore',
    'repro',
    'tahoe',
    'mldonkey',
]

REMOVED_FILES = [
    '/etc/apt/preferences.d/50freedombox3.pref',
    '/etc/apache2/sites-available/plinth.conf',
    '/etc/apache2/sites-available/plinth-ssl.conf',
    '/etc/security/access.d/10freedombox-performance.conf',
    '/etc/security/access.d/10freedombox-security.conf',
]

LOCALE_PATHS = ['plinth/locale']


class DjangoCommand(Command):
    """Setup command to run a Django management command."""
    user_options: list = []

    def initialize_options(self):
        """Declare the options for this command."""
        pass

    def finalize_options(self):
        """Declare options dependent on others."""
        pass

    def run(self):
        """Execute the command."""
        import django
        from django.conf import settings

        settings.configure(LOCALE_PATHS=LOCALE_PATHS)
        django.setup()

        # Trick the commands to use the settings properly
        os.environ['DJANGO_SETTINGS_MODULE'] = 'x-never-used'


class CompileTranslations(DjangoCommand):
    """New command to compile .po translation files."""
    description = "compile .po translation files into .mo files" ""

    def run(self):
        """Execute the command."""
        DjangoCommand.run(self)

        from django.core.management import call_command
        call_command('compilemessages', verbosity=1)


class UpdateTranslations(DjangoCommand):
    """New command to update .po translation files."""
    description = "update .po translation files from source code" ""

    def run(self):
        """Execute the command."""
        DjangoCommand.run(self)

        from django.core.management import call_command
        call_command('makemessages', all=True, domain='django', keep_pot=True,
                     verbosity=1)


class CustomBuild(build):
    """Override build command to add a subcommand for translations."""
    sub_commands = [('compile_translations', None)] + build.sub_commands


class CustomClean(clean):
    """Override clean command to clean doc, locales, and egg-info."""

    def run(self):
        """Execute clean command"""
        subprocess.check_call(['rm', '-rf', 'Plinth.egg-info/'])
        subprocess.check_call(['make', '-C', 'doc', 'clean'])

        for dir_path, dir_names, file_names in os.walk('plinth/locale/'):
            for file_name in file_names:
                if file_name.endswith('.mo'):
                    file_path = os.path.join(dir_path, file_name)
                    log.info("removing '%s'", file_path)
                    subprocess.check_call(['rm', '-f', file_path])

        clean.run(self)


class CustomInstall(install):
    """Override install command."""

    def run(self):
        for app in DISABLED_APPS_TO_REMOVE:
            file_path = pathlib.Path(ENABLED_APPS_PATH) / app
            if file_path.exists():
                log.info("removing '%s'", str(file_path))
                subprocess.check_call(['rm', '-f', str(file_path)])

        for path in REMOVED_FILES:
            if pathlib.Path(path).exists():
                log.info('removing %s', path)
                subprocess.check_call(['rm', '-f', path])

        install.run(self)


class CustomInstallData(install_data):
    """Override install command to allow directory creation and copy"""

    def _run_doc_install(self):
        """Install documentation"""
        command = ['make', '-j', '8', '-C', 'doc', 'install']
        if self.root:
            root = os.path.abspath(self.root)
            command.append(f'DESTDIR={root}')

        subprocess.check_call(command)

    def run(self):
        """Execute install command"""
        self._run_doc_install()

        install_data.run(self)  # Old style base class

        # Create empty directories
        for directory in DIRECTORIES_TO_CREATE:
            if self.root:
                directory = change_root(self.root, directory)

            if not os.path.exists(directory):
                log.info("creating directory '%s'", directory)
                os.makedirs(directory)

        # Recursively overwrite directories
        for target, source in DIRECTORIES_TO_COPY:
            if self.root:
                target = change_root(self.root, target)

            if os.path.exists(target):
                remove_tree(target)

            log.info("recursive copy '%s' to '%s'", source, target)
            shutil.copytree(source, target, symlinks=True)


def _ignore_data_file(file_name):
    """Ignore common patterns in data files and directories."""
    ignore_patterns = [
        r'\.log$', r'\.pid$', r'\.py.bak$', r'\.pyc$', r'\.pytest_cache$',
        r'\.sqlite3$', r'\.swp$', r'^#', r'^\.', r'^__pycache__$',
        r'^sessionid\w*$', r'~$', r'django-secret.key'
    ]
    for pattern in ignore_patterns:
        if re.match(pattern, file_name):
            return True

    return False


def _gather_data_files():
    """Return a list data files are required by setuptools.setup().

    - Automatically infer the target directory by looking at the relative path
      of a file.

    - Allow each app to have it's own folder for data files.

    - Ignore common backup files.

    """
    data_files = collections.defaultdict(list)
    crawl_directories = ['data']
    with os.scandir('plinth/modules/') as iterator:
        for entry in iterator:
            if entry.is_dir():
                crawl_directories.append(os.path.join(entry.path, 'data'))

    for crawl_directory in crawl_directories:
        crawl_directory = crawl_directory.rstrip('/')
        for path, _, file_names in os.walk(crawl_directory):
            target_directory = path[len(crawl_directory):]
            if _ignore_data_file(os.path.basename(path)):
                continue

            for file_name in file_names:
                if _ignore_data_file(file_name):
                    continue

                data_files[target_directory].append(
                    os.path.join(path, file_name))

    return list(data_files.items())


find_packages = setuptools.PEP420PackageFinder.find
setuptools.setup(
    name='Plinth',
    version=__version__,
    description='A web front end for administering FreedomBox',
    author='FreedomBox Authors',
    author_email='freedombox-discuss@lists.alioth.debian.org',
    url='https://freedombox.org',
    packages=find_packages(include=['plinth', 'plinth.*'],
                           exclude=['*.templates']),
    scripts=['bin/plinth'],
    license='COPYING.md',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: End Users/Desktop',
        'License :: DFSG approved',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Unix Shell',
        'Topic :: Communications',
        'Topic :: Communications :: Chat',
        'Topic :: Communications :: Chat :: Internet Relay Chat',
        'Topic :: Communications :: File Sharing',
        'Topic :: Internet',
        'Topic :: Internet :: Name Service (DNS)'
        'Topic :: Internet :: Proxy Servers',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki',
        'Topic :: Internet :: WWW/HTTP :: WSGI',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Office/Business',
        'Topic :: Office/Business :: Scheduling',
        'Topic :: Security',
        'Topic :: System'
        'Topic :: System :: Archiving',
        'Topic :: System :: Archiving :: Backup',
        'Topic :: System :: Distributed Computing'
        'Topic :: System :: Filesystems',
        'Topic :: System :: Installation/Setup',
        'Topic :: System :: Networking',
        'Topic :: System :: Networking :: Firewalls',
        'Topic :: System :: Operating System',
        'Topic :: System :: Software Distribution'
        'Topic :: System :: Systems Administration',
        'Topic :: System :: Systems Administration :: Authentication/Directory',
        'Topic :: System :: Systems Administration :: Authentication/Directory :: LDAP   ',
        'Topic :: System :: System Shells',
    ],
    setup_requires=['pytest-runner', 'setuptools-git'],
    install_requires=[
        'cherrypy >= 3.0',
        'configobj',
        'django >= 1.11.0',
        'django-bootstrap-form',
        'django-simple-captcha',
        'django-stronghold >= 0.3.0',
        'psutil',
        'python-apt',
        'python-augeas',
        'requests',
        'ruamel.yaml',
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-django',
        'flake8',
        'requests',
        'tomli',
    ],
    package_data={
        '': ['templates/*', 'static/**', 'locale/*/LC_MESSAGES/*.mo']
    },
    exclude_package_data={'': ['*/data/*']},
    data_files=_gather_data_files() +
    [('/usr/share/plinth/actions', glob.glob(os.path.join('actions',
                                                          '[a-z]*'))),
     ('/usr/share/man/man1', ['doc/plinth.1'])],
    cmdclass={
        'install': CustomInstall,
        'build': CustomBuild,
        'clean': CustomClean,
        'compile_translations': CompileTranslations,
        'install_data': CustomInstallData,
        'update_translations': UpdateTranslations,
    },
)
