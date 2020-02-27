# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Overridden AppConfig from django-axes to avoid monkey-patched LoginView
"""

from django import apps


class AppConfig(apps.AppConfig):
    name = 'axes'

    def ready(self):
        # Signals must be loaded for axes to get the login_failed signals
        from axes import signals  # noqa pylint: disable=unused-import isort:skip
