# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for minetest app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.minetest]


class TestMinetestApp(BaseAppTests):
    app_name = 'minetest'
    has_service = True
    has_web = False
