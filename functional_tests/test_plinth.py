# SPDX-License-Identifier: AGPL-3.0-or-later

import pytest

try:
    from pytest_bdd import scenarios
except ImportError:
    pytestmark = pytest.mark.skip(reason='pytest_bdd is not installed')
else:
    from step_definitions.application import *
    from step_definitions.interface import *
    from step_definitions.service import *
    from step_definitions.site import *
    from step_definitions.system import *

    # Mark all tests are functional
    pytestmark = pytest.mark.functional

    scenarios('features')
