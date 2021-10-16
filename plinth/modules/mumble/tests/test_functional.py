# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for mumble app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.mumble]


class TestMumbleApp(BaseAppTests):
    app_name = 'mumble'
    has_service = True
    has_web = False

    # TODO: Requires a valid domain with certificates to complete setup.
    check_diagnostics = False

    # TODO: Improve test_backup_restore to actually check that data such
    # as rooms, identity or certificates are restored.
