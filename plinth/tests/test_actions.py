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
Test module for actions utilities that modify configuration.

Verify that privileged actions perform as expected. See actions.py for a full
description of the expectations.

"""

import os
import pathlib
import shutil
import tempfile

import pytest

import apt_pkg
from plinth import cfg
from plinth.actions import run, superuser_run
from plinth.errors import ActionError


@pytest.fixture(scope='module', autouse=True)
def actions_test_setup():
    """Setup a temporary directory for testing actions.

    Copy system commands ``echo`` and ``id`` into actions directory during
    testing.

    """
    with tempfile.TemporaryDirectory() as tmp_directory:
        old_actions_dir = cfg.actions_dir
        cfg.actions_dir = str(tmp_directory)

        actions_dir = pathlib.Path(__file__).parent / '../../actions'
        shutil.copy(str(actions_dir / 'packages'), str(tmp_directory))
        shutil.copy(str(actions_dir / 'test_path'), str(tmp_directory))
        shutil.copy('/bin/echo', str(tmp_directory))
        shutil.copy('/usr/bin/id', str(tmp_directory))

        yield
        cfg.actions_dir = old_actions_dir


def notest_run_as_root():
    """1. Privileged actions run as root. """
    assert superuser_run('id', ['-ur'])[0].strip() == '0'  # user 0 is root


def test_breakout_actions_dir():
    """2. The actions directory can't be changed at run time.

    Can't currently be tested, as the actions directory is hardcoded.
    """


def test_breakout_up():
    """3A. Users can't call actions above the actions directory.

    Tests both a relative and a literal path.
    """
    for action in ('../echo', '/bin/echo'):
        with pytest.raises(ValueError):
            run(action, ['hi'])


def test_breakout_down():
    """3B. Users can't call actions beneath the actions directory."""
    action = 'directory/echo'
    with pytest.raises(ValueError):
        superuser_run(action)


def test_breakout_actions():
    """3C. Actions can't be used to run other actions.

    If multiple actions are specified, bail out.
    """
    # Counting is safer than actual badness.
    actions = ('echo ""; echo $((1+1))', 'echo "" && echo $((1+1))',
               'echo "" || echo $((1+1))')
    options = ('good', '')

    for action in actions:
        for option in options:
            with pytest.raises(ValueError):
                run(action, [option])


def test_breakout_option_string():
    """3D. Option strings can't be used to run other actions.

    Verify that shell control characters aren't interpreted.
    """
    options = ('; echo hello', '&& echo hello', '|| echo hello',
               '& echo hello', r'\; echo hello', '| echo hello',
               r':;!&\/$%@`"~#*(){}[]|+=')
    for option in options:
        output = run('echo', [option])
        output = output.rstrip('\n')
        assert option == output


def test_breakout_option_list():
    """3D. Option lists can't be used to run other actions.

    Verify that shell control characters aren't interpreted in
    option lists.
    """
    option_lists = (
        (';', 'echo', 'hello'),
        ('&&', 'echo', 'hello'),
        ('||', 'echo', 'hello'),
        ('&', 'echo', 'hello'),
        (r'\;', 'echo'
         'hello'),
        ('|', 'echo', 'hello'),
        ('', 'echo', '', 'hello'),  # Empty option argument
        tuple(r':;!&\/$%@`"~#*(){}[]|+='))
    for options in option_lists:
        output = run('echo', options)
        output = output.rstrip('\n')
        expected_output = ' '.join(options)
        assert output == expected_output


def test_multiple_options_and_output():
    """4. Multiple options can be provided as a list or as a tuple.

    5. Output is returned from the command.
    """
    options = '1 2 3 4 5 6 7 8 9'

    output = run('echo', options.split())
    output = output.rstrip('\n')
    assert options == output

    output = run('echo', tuple(options.split()))
    output = output.rstrip('\n')
    assert options == output


@pytest.mark.usefixtures('needs_root')
def test_is_package_manager_busy():
    """Test the behavior of `is-package-manager-busy` in both locked and
    unlocked states of the dpkg lock file."""

    apt_pkg.init()  # initialize apt_pkg module

    # In the locked state, the lsof command returns 0.
    # Hence no error is thrown.
    with apt_pkg.SystemLock():
        superuser_run('packages', ['is-package-manager-busy'])

    # In the unlocked state, the lsof command returns 1.
    # An ActionError is raised in this case.
    with pytest.raises(ActionError):
        superuser_run('packages', ['is-package-manager-busy'])


@pytest.mark.usefixtures('develop_mode', 'needs_root')
def test_action_path(monkeypatch):
    """Test that in development mode, python action scripts get the
    correct PYTHONPATH"""
    monkeypatch.setitem(os.environ, 'PYTHONPATH', '')
    plinth_path = run('test_path').strip()
    su_plinth_path = superuser_run('test_path').strip()
    assert plinth_path.startswith(cfg.root)
    assert plinth_path == su_plinth_path
