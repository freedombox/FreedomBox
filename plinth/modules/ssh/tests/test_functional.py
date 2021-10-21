# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for ssh app.
"""

import pytest

from plinth.tests.functional import BaseAppTests

pytestmark = [pytest.mark.system, pytest.mark.ssh]


class TestSshApp(BaseAppTests):
    app_name = 'ssh'
    has_service = True
    has_web = False

    # TODO: Improve test_backup_restore to actually check that earlier
    # ssh certificate has been restored.
