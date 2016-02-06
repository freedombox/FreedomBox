#!/usr/bin/python3
#
# This file is part of Plinth.
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
Plinth setup file
"""

from distutils import log
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.core import Command
from distutils.util import change_root
import glob
import os
import setuptools
import shutil
import subprocess

from plinth import __version__
from plinth.tests.coverage import coverage


DIRECTORIES_TO_CREATE = [
    '/var/lib/plinth',
    '/var/lib/plinth/sessions',
    '/var/log/plinth',
]

DIRECTORIES_TO_COPY = [
    ('/usr/share/plinth/static', 'static'),
    ('/usr/share/doc/plinth', 'doc'),
]

LOCALE_PATHS = [
    'plinth/locale'
]


class DjangoCommand(Command):
    """Setup command to run a Django management command."""
    user_options = []

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
    description = "compile .po translation files into .mo files"""

    def run(self):
        """Execute the command."""
        DjangoCommand.run(self)

        from django.core.management import call_command
        call_command('compilemessages', verbosity=1)


class UpdateTranslations(DjangoCommand):
    """New command to update .po translation files."""
    description = "update .po translation files from source code"""

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


class CustomInstallData(install_data):
    """Override install command to allow directory creation and copy"""
    def run(self):
        """Execute install command"""
        subprocess.check_call(['make', '-C', 'doc'])

        install_data.run(self)  # Old style base class

        # Create empty directories
        for directory in DIRECTORIES_TO_CREATE:
            if self.root:
                directory = change_root(self.root, directory)

            if not os.path.exists(directory):
                log.info("creating directory '%s'", directory)
                os.makedirs(directory)

        # Recursively copy directories
        for target, source in DIRECTORIES_TO_COPY:
            if self.root:
                target = change_root(self.root, target)

            if not os.path.exists(target):
                log.info("recursive copy '%s' to '%s'", source, target)
                shutil.copytree(source, target, symlinks=True)


find_packages = setuptools.PEP420PackageFinder.find
setuptools.setup(
    name='Plinth',
    version=__version__,
    description='A web front end for administering FreedomBox',
    author='Plinth Authors',
    author_email='freedombox-discuss@lists.alioth.debian.org',
    url='http://freedomboxfoundation.org',
    packages=find_packages(include=['plinth', 'plinth.*'],
                           exclude=['*.templates']),
    scripts=['bin/plinth'],
    test_suite='plinth.tests.runtests.run_tests',
    license='COPYING',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: End Users/Desktop',
        'License :: DFSG approved',
        'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Unix Shell',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: System :: Systems Administration',
    ],
    setup_requires=['setuptools-git'],
    install_requires=[
        'cherrypy >= 3.0',
        'django >= 1.7.0',
        'django-bootstrap-form',
        'django-stronghold',
        'psutil',
        'python-augeas',
        'pyyaml',
    ],
    tests_require=['coverage >= 3.7'],
    include_package_data=True,
    package_data={'plinth': ['templates/*',
                             'modules/*/templates/*',
                             'locale/*/LC_MESSAGES/*.[pm]o']},
    data_files=[('/etc/init.d', ['data/etc/init.d/plinth']),
                ('/usr/lib/firewalld/services/',
                 glob.glob('data/usr/lib/firewalld/services/*.xml')),
                ('/usr/lib/freedombox/setup.d/',
                 ['data/usr/lib/freedombox/setup.d/86_plinth']),
                ('/usr/lib/freedombox/first-run.d',
                 ['data/usr/lib/freedombox/first-run.d/90_firewall']),
                ('/etc/apache2/conf-available',
                 glob.glob('data/etc/apache2/conf-available/*.conf')),
                ('/etc/apache2/sites-available',
                 glob.glob('data/etc/apache2/sites-available/*.conf')),
                ('/etc/ikiwiki',
                 glob.glob('data/etc/ikiwiki/*.setup')),
                ('/etc/sudoers.d', ['data/etc/sudoers.d/plinth']),
                ('/lib/systemd/system',
                 ['data/lib/systemd/system/plinth.service']),
                ('/usr/share/plinth/actions',
                 glob.glob(os.path.join('actions', '*'))),
                ('/usr/share/man/man1', ['doc/plinth.1']),
                ('/etc/plinth', ['data/etc/plinth/plinth.config']),
                ('/usr/share/augeas/lenses',
                 ['data/usr/share/augeas/lenses/pagekite.aug']),
                ('/usr/share/augeas/lenses/tests',
                 ['data/usr/share/augeas/lenses/tests/test_pagekite.aug']),
                ('/etc/plinth/modules-enabled',
                 glob.glob(os.path.join('data/etc/plinth/modules-enabled',
                                        '*')))],
    cmdclass={
        'build': CustomBuild,
        'clean': CustomClean,
        'compile_translations': CompileTranslations,
        'install_data': CustomInstallData,
        'test_coverage': coverage.CoverageCommand,
        'update_translations': UpdateTranslations,
    },
)
