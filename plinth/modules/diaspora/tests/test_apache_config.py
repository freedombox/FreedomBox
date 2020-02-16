# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test Apache configuration generation for diaspora*
"""

import os
import tempfile

from plinth.modules import diaspora


def test_generate_apache_configuration():
    """Test that Apache configuration is created properly."""
    with tempfile.NamedTemporaryFile() as conf_file:
        diaspora.generate_apache_configuration(conf_file.name,
                                               'freedombox.rocks')

        assert os.stat(conf_file.name).st_size != 0

        with open(conf_file.name) as file_handle:
            contents = file_handle.read()

        assert all(
            word in contents
            for word in ['VirtualHost', 'Location', 'Directory', 'assets'])
