# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for roundcube app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.roundcube]


class TestRoundcubeApp(BaseAppTests):
    app_name = 'roundcube'
    has_service = False
    has_web = True
