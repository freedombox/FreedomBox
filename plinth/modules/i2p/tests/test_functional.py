# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for i2p app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.i2p]


class TestI2pApp(BaseAppTests):
    app_name = 'i2p'
    has_service = True
    has_web = True
