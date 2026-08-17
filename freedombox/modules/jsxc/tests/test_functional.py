# SPDX-License-Identifier: AGPL-3.0-or-later
"""Functional, browser based tests for jsxc app."""

import pytest

from plinth.tests import functional

pytestmark = [pytest.mark.apps, pytest.mark.jsxc]


class TestJSXCApp(functional.BaseAppTests):
    app_name = 'jsxc'
