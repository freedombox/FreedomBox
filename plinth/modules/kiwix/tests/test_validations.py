# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix validations.
"""

import unittest
from plinth.modules import kiwix


class TestValidations(unittest.TestCase):

    def test_add_file_with_invalid_extension(self):
        self.assertRaises(ValueError,
                          lambda: kiwix.validate_file_name('wikipedia.zip'))

        # We don't support the legacy format of split zim files.
        self.assertRaises(
            ValueError, lambda: kiwix.validate_file_name(
                'wikipedia_en_all_maxi_2022-05.zima'))

        kiwix.validate_file_name('wikipedia_en_all_maxi_2022-05.zim')
