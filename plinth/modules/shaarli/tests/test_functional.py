# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for shaarli app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.shaarli]


class TestShaarliApp(BaseAppTests):
    app_name = 'shaarli'
    has_service = False
    has_web = True
    # TODO: Complete Shaarli setup.
    # TODO: Add, edit, remove bookmark.
