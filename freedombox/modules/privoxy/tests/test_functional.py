# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for privoxy app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.privoxy]


class TestPrivoxyApp(BaseAppTests):
    app_name = 'privoxy'
    has_service = True
    has_web = False
