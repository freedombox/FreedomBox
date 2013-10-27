#! /usr/bin/env python
# -*- mode: python; mode: auto-fill; fill-column: 80 -*-

import sys
from actions.privilegedactions import privilegedaction_run
import unittest

class TestPrivileged(unittest.TestCase):
    """Verify that privileged actions perform as expected:

    1. Privileged actions run as root.

    2. Only whitelisted privileged actions can run.

       A. Actions can't be used to run other actions:

          $ action="echo 'hi'; rm -rf /"
          $ $action

       B. Options can't be used to run other actions:

          $ options="hi'; rm -rf /;'"
          $ "echo " + "'$options'"

       C. Scripts in a directory above the actions directory can't be run.

       D. Scripts in a directory beneath the actions directory can't be run.

    3. The actions directory can't be changed at run time.

    """
    def test_run_as_root(self):
        """1. Privileged actions run as root.

        """
        self.assertEqual(
            "0", # user 0 is root
            privilegedaction_run("id", "-ur")[0].strip())

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
                privilegedaction_run(arg, options)

    def test_breakout_down(self):
        """3B. Users can't call actions beneath the actions directory."""
        action="directory/echo"

        self.assertRaises(ValueError, privilegedaction_run, action)

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
                    output = privilegedaction_run(action, option)

                    print(output)

                    # if it doesn't error, we'd better not evaluate the data.
                    self.assertFalse("2" in output[0])

    def test_breakout_options(self):
        """3D. Options can't be used to run other actions."""

        action = "echo"
        # counting is safer than actual badness.
        options = "good; echo $((1+1))"

        output, error = privilegedaction_run(action, options)

        self.assertFalse("2" in output)

if __name__ == "__main__":
    unittest.main()

