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
from distutils.command.clean import clean
from distutils.command.install_data import install_data
from distutils.util import change_root
import glob
import os
import setuptools
import shutil
import subprocess

from plinth import __version__
from plinth.tests.coverage import test_coverage


DIRECTORIES_TO_CREATE = [
    '/var/lib/plinth',
    '/var/lib/plinth/sessions',
    '/var/log/plinth',
]

DIRECTORIES_TO_COPY = [
    ('/usr/share/plinth/static', 'static'),
    ('/usr/share/doc/plinth', 'doc'),
]


class CustomClean(clean):
    """Override clean command to clean documentation directory"""
    def run(self):
        """Execute clean command"""
        subprocess.check_call(['make', '-C', 'doc', 'clean'])

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
    test_suite='plinth.tests.TEST_SUITE',
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
        'pygobject'
    ],
    tests_require=['coverage >= 3.7'],
    include_package_data=True,
    package_data={'plinth': ['templates/*',
                             'modules/*/templates/*']},
    data_files=[('/etc/init.d', ['data/etc/init.d/plinth']),
                ('/usr/lib/freedombox/setup.d/',
                 ['data/usr/lib/freedombox/setup.d/86_plinth']),
                ('/usr/lib/freedombox/first-run.d',
                 ['data/usr/lib/freedombox/first-run.d/90_firewall']),
                ('/etc/apache2/sites-available',
                 ['data/etc/apache2/sites-available/plinth.conf',
                  'data/etc/apache2/sites-available/plinth-ssl.conf']),
                ('/etc/sudoers.d', ['data/etc/sudoers.d/plinth']),
                ('/usr/share/plinth/actions',
                 glob.glob(os.path.join('actions', '*'))),
                ('/usr/share/man/man1', ['doc/plinth.1']),
                ('/etc/plinth', ['data/etc/plinth/plinth.config']),
                ('/etc/plinth/modules-enabled',
                 glob.glob(os.path.join('data/etc/plinth/modules-enabled',
                                        '*')))],
    cmdclass={
        'clean': CustomClean,
        'install_data': CustomInstallData,
        'test_coverage': test_coverage.TestCoverageCommand
    },
)
