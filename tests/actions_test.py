#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

from actions import superuser_run, run
import shlex
import subprocess
import sys
import unittest

class TestPrivileged(unittest.TestCase):
    """Verify that privileged actions perform as expected.

    See actions.py for a full description of the expectations.

    """
    def test_run_as_root(self):
        """1. Privileged actions run as root.

        """
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

                    # if it somewhow doesn't error, we'd better not evaluate the
                    # data.
                    self.assertFalse("2" in output[0])

    def test_breakout_option_string(self):
        """3D. Option strings can't be used to run other actions.

        Verify that shell control characters aren't interpreted.

        """
        action = "echo"
        # counting is safer than actual badness.
        options = "good; echo $((1+1))"

        output, error = run(action, options)

        self.assertFalse("2" in output)

    def test_breakout_option_list(self):
        """3D. Option lists can't be used to run other actions.

        Verify that only a string of options is accepted and that we can't just
        tack additional shell control characters onto the list.

        """
        action = "echo"
        # counting is safer than actual badness.
        options = ["good", ";", "echo $((1+1))"]

        output, error = run(action, options)

        # we'd better not evaluate the data.
        self.assertFalse("2" in output)

    def test_multiple_options(self):
        """4. Multiple options can be provided as a list.

        """
        self.assertEqual(
            subprocess.check_output(shlex.split("id -ur")).strip(),
            run("id", ["-u" ,"-r"])[0].strip())

if __name__ == "__main__":
    unittest.main()
