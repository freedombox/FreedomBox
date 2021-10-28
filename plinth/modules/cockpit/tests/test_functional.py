# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for cockpit app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.cockpit]


class TestCockpitApp(BaseAppTests):
    app_name = 'cockpit'
    has_service = True
    has_web = True
