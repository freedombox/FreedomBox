#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

from actions import superuser_run, run
import os
import shlex
import subprocess
import unittest

import cfg

ROOT_DIR = os.path.split(os.path.abspath(os.path.split(__file__)[0]))[0]
cfg.actions_dir = os.path.join(ROOT_DIR, 'actions')

class TestPrivileged(unittest.TestCase):
    """Verify that privileged actions perform as expected.

    See actions.py for a full description of the expectations.

    Symlink to ``echo`` and ``id`` during testing.

    """
    @classmethod
    def setUpClass(cls):
        os.symlink("/bin/echo", "actions/echo")
        os.symlink("/usr/bin/id", "actions/id")

    @classmethod
    def tearDownClass(cls):
        os.remove("actions/echo")
        os.remove("actions/id")

    def notest_run_as_root(self):
        """1. Privileged actions run as root. """
        # TODO: it's not allowed to call a symlink in the actions dir anymore
        self.assertEqual(
            "0", # user 0 is root
            superuser_run("id", "-ur")[0].strip())

    def test_breakout_actions_dir(self):
        """2. The actions directory can't be changed at run time.

        Can't currently be tested, as the actions directory is hardcoded.

        """
        pass

    def test_breakout_up(self):
        """3A. Users can't call actions above the actions directory.

        Tests both a relative and a literal path.

        """
        options="hi"

        for arg in ("../echo", "/bin/echo"):
            with self.assertRaises(ValueError):
                run(arg, options)

    def test_breakout_down(self):
        """3B. Users can't call actions beneath the actions directory."""
        action="directory/echo"

        self.assertRaises(ValueError, superuser_run, action)

    def test_breakout_actions(self):
        """3C. Actions can't be used to run other actions.

        If multiple actions are specified, bail out.

        """
        # counting is safer than actual badness.
        actions = ("echo ''; echo $((1+1))",
                   "echo '' && echo $((1+1))",
                   "echo '' || echo $((1+1))")
        options = ("good", "")

        for action in actions:
            for option in options:
                with self.assertRaises(ValueError):
                    output = run(action, option)
                    # if it somewhow doesn't error, we'd better not evaluate
                    # the data.
                    self.assertFalse("2" in output[0])

    def test_breakout_option_string(self):
        """3D. Option strings can't be used to run other actions.
        Verify that shell control characters aren't interpreted.
        """
        action = "echo"
        # counting is safer than actual badness.
        options = "good; echo $((1+1))"
        self.assertRaises(ValueError, run, action, options)

    def test_breakout_option_list(self):
        """3D. Option lists can't be used to run other actions.
        Verify that only a string of options is accepted and that we can't just
        tack additional shell control characters onto the list.
        """
        action = "echo"
        # counting is safer than actual badness.
        options = ["good", ";", "echo $((1+1))"]
        # we'd better not evaluate the data.
        self.assertRaises(ValueError, run, action, options)

    def notest_multiple_options(self):
        """ 4. Multiple options can be provided as a list. """
        # TODO: it's not allowed to call a symlink in the actions dir anymore
        self.assertEqual(
            subprocess.check_output(shlex.split("id -ur")).strip(),
            run("id", ["-u" ,"-r"])[0].strip())

if __name__ == "__main__":
    unittest.main()
