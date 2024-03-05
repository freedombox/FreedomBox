# SPDX-License-Identifier: AGPL-3.0-or-later
"""
FreedomBox app for api for android app.
"""

from plinth import app as app_module


class ApiApp(app_module.App):
    """FreedomBox app for API for Android app."""

    app_id = 'api'

    _version = 1

    def __init__(self) -> None:
        """Create components for the app."""
        super().__init__()

        info = app_module.Info(app_id=self.app_id, version=self._version,
                               is_essential=True)
        self.add(info)

    def setup(self, old_version):
        """Install and configure the app."""
        super().setup(old_version)
        self.enable()
