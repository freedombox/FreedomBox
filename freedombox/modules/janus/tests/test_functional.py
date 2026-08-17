# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for Janus app.
"""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.janus]


class TestJanusApp(functional.BaseAppTests):
    app_name = 'janus'
    has_service = True
    has_web = True
