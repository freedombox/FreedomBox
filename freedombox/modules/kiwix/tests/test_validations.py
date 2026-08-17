# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for Kiwix validations.
"""

import pytest

from plinth.modules import kiwix


def test_add_file_with_invalid_extension():
    """Test that adding a file with invalid fails as expected."""
    with pytest.raises(ValueError):
        kiwix.validate_file_name('wikipedia.zip')

    # We don't support the legacy format of split zim files.
    with pytest.raises(ValueError):
        kiwix.validate_file_name('wikipedia_en_all_maxi_2022-05.zima')

    kiwix.validate_file_name('wikipedia_en_all_maxi_2022-05.zim')
