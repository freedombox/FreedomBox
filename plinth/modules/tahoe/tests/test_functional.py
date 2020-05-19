# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Functional, browser based tests for tahoe app.
"""

from pytest_bdd import scenarios

scenarios('tahoe.feature')
