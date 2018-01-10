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
Test module for actions utilities that modify configuration.
"""

import apt_pkg
import os
import shutil
import tempfile
import unittest

from plinth.errors import ActionError
from plinth.actions import superuser_run, run
from plinth import cfg


class TestPrivileged(unittest.TestCase):
    """Verify that privileged actions perform as expected.

    See actions.py for a full description of the expectations.

    Symlink to ``echo`` and ``id`` during testing.
    """
    @classmethod
    def setUpClass(cls):
        """Initial setup for all the classes."""
        cls.action_directory = tempfile.TemporaryDirectory()
        cfg.actions_dir = cls.action_directory.name

        shutil.copy(os.path.join(os.path.dirname(__file__), '..', '..', 'actions', 'packages'), cfg.actions_dir)
        shutil.copy('/bin/echo', cfg.actions_dir)
        shutil.copy('/usr/bin/id', cfg.actions_dir)

    @classmethod
    def tearDownClass(cls):
        """Cleanup after all the tests are completed."""
        cls.action_directory.cleanup()

    def notest_run_as_root(self):
        """1. Privileged actions run as root. """
        self.assertEqual(
            '0',  # user 0 is root
            superuser_run('id', ['-ur'])[0].strip())

    def test_breakout_actions_dir(self):
        """2. The actions directory can't be changed at run time.

        Can't currently be tested, as the actions directory is hardcoded.
        """
        pass

    def test_breakout_up(self):
        """3A. Users can't call actions above the actions directory.

        Tests both a relative and a literal path.
        """
        for action in ('../echo', '/bin/echo'):
            with self.assertRaises(ValueError):
                run(action, ['hi'])

    def test_breakout_down(self):
        """3B. Users can't call actions beneath the actions directory."""
        action = 'directory/echo'

        self.assertRaises(ValueError, superuser_run, action)

    def test_breakout_actions(self):
        """3C. Actions can't be used to run other actions.

        If multiple actions are specified, bail out.
        """
        # Counting is safer than actual badness.
        actions = ('echo ""; echo $((1+1))',
                   'echo "" && echo $((1+1))',
                   'echo "" || echo $((1+1))')
        options = ('good', '')

        for action in actions:
            for option in options:
                with self.assertRaises(ValueError):
                    run(action, [option])

    def test_breakout_option_string(self):
        """3D. Option strings can't be used to run other actions.

        Verify that shell control characters aren't interpreted.
        """
        options = ('; echo hello',
                   '&& echo hello',
                   '|| echo hello',
                   '& echo hello',
                   r'\; echo hello',
                   '| echo hello',
                   r':;!&\/$%@`"~#*(){}[]|+=')
        for option in options:
            output = run('echo', [option])
            output = output.rstrip('\n')
            self.assertEqual(option, output)

    def test_breakout_option_list(self):
        """3D. Option lists can't be used to run other actions.

        Verify that shell control characters aren't interpreted in
        option lists.
        """
        option_lists = ((';', 'echo', 'hello'),
                        ('&&', 'echo', 'hello'),
                        ('||', 'echo', 'hello'),
                        ('&', 'echo', 'hello'),
                        (r'\;', 'echo' 'hello'),
                        ('|', 'echo', 'hello'),
                        ('', 'echo', '', 'hello'),  # Empty option argument
                        tuple(r':;!&\/$%@`"~#*(){}[]|+='))
        for options in option_lists:
            output = run('echo', options)
            output = output.rstrip('\n')
            expected_output = ' '.join(options)
            self.assertEqual(output, expected_output)

    def test_multiple_options_and_output(self):
        """4. Multiple options can be provided as a list or as a tuple.

        5. Output is returned from the command.
        """
        options = '1 2 3 4 5 6 7 8 9'

        output = run('echo', options.split())
        output = output.rstrip('\n')
        self.assertEqual(options, output)

        output = run('echo', tuple(options.split()))
        output = output.rstrip('\n')
        self.assertEqual(options, output)

    def test_error_handling_for_superuser(self):
        """Test that errors are raised only when expected."""
        with apt_pkg.SystemLock():
            with self.assertRaises(ActionError):
                superuser_run('packages', ['is-package-manager-busy'],
                              expecting_error=True)
            with self.assertRaises(ActionError):
                superuser_run('packages', ['is-package-manager-busy'],
                              expecting_error=False)
            with self.assertRaises(ActionError):
                superuser_run('packages', ['is-package-manager-busy'])
