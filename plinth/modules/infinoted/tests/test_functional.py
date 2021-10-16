# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for infinoted app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.infinoted]


class TestInfinotedApp(BaseAppTests):
    app_name = 'infinoted'
    has_service = True
    has_web = False
