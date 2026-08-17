# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for minidlna app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.minidlna]


class TestMinidlnaApp(BaseAppTests):
    app_name = 'minidlna'
    has_service = True
    has_web = False
