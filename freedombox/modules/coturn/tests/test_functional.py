# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for coturn app.
"""

import pytest
from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.coturn]


class TestCoturnApp(BaseAppTests):
    app_name = 'coturn'
    has_service = True
    has_web = False

    # TODO: Requires a valid domain with certificates to complete setup.
    check_diagnostics = False

    # TODO: Improve backup test by checking that secret and domain did
    # not change
