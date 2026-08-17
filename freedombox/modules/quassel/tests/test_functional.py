# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for quassel app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.apps, pytest.mark.quassel]


class TestQuasselApp(BaseAppTests):
    app_name = 'quassel'
    has_service = True
    has_web = False

    # TODO: Improve test_backup_restore to actually check that data
    # configured servers is restored.
