# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for performance app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.system, pytest.mark.performance]


class TestPerformanceApp(BaseAppTests):
    app_name = 'performance'
    has_service = True
    has_web = False
