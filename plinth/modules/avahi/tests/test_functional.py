# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for avahi app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.system, pytest.mark.essential, pytest.mark.avahi]


class TestAvahiApp(BaseAppTests):
    app_name = 'avahi'
    has_service = True
    has_web = False
