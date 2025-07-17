"""Components for managing configuration files."""

import logging
import pathlib

from django.utils.translation import gettext_noop

from plinth.diagnostic_check import (DiagnosticCheck,
                                     DiagnosticCheckParameters, Result)
from plinth.privileged import config as privileged

from . import app as app_module

logger = logging.getLogger(__name__)


class DropinConfigs(app_module.FollowerComponent):
    """Component to manage config files dropped into /etc.

    When configuring a daemon, it is often simpler to ship a configuration file
    into the daemon's configuration directory. However, if the user modifies
    this configuration file and freedombox ships a new version of this
    configuration file, then a conflict arises between user's changes and
    changes in the new version of configuration file shipped by freedombox.
    This leads to freedombox package getting marked by unattended-upgrades as
    not automatically upgradable. Dpkg's solution of resolving the conflicts is
    to present the option to the user which is also not acceptable.

    Further, if a package is purged from the system, sometimes the
    configuration directories are fully removed by deb's scripts. This removes
    files installed by freedombox package. Dpkg treats these files as if user
    has explictly removed them and may lead to a configuration conflict
    described above.

    The approach freedombox takes to address these issues is using this
    component. Files are shipped into /usr/share/freedombox/etc/ instead of
    /etc/ (keeping the subpath unchanged). Then when an app is enabled, a
    symlink or copy is created from the /usr/share/freedombox/etc/ into /etc/.
    This way, user's understand the configuration file is not meant to be
    edited. Even if they do, next upgrade of freedombox package will silently
    overwrite those changes without causing merge conflicts. Also when purging
    a package removes entire configuration directory, only symlinks/copies are
    lost. They will recreated when the app is reinstalled/enabled.
    """

    ROOT = '/'  # To make writing tests easier
    DROPIN_CONFIG_ROOT = '/usr/share/freedombox/'

    def __init__(self, component_id, etc_paths=None, copy_only=False):
        """Initialize the drop-in configuration component.

        component_id should be a unique ID across all components of an app and
        across all components.

        etc_paths is a list of all drop-in configuration files as absolute
        paths in /etc/ which need to managed by this component. For each of the
        paths, it is expected that the actual configuration file exists in
        /usr/share/freedombox/etc/. A link to the file or copy of the file is
        created in /etc/ when app is enabled and the link or file is removed
        when app is disabled. For example, if etc_paths contains
        /etc/apache/conf-enabled/myapp.conf then
        /usr/share/freedombox/etc/apache/conf-enabled/myapp.conf must be
        shipped and former path will be link to or be a copy of the latter when
        app is enabled.
        """
        super().__init__(component_id)
        self.etc_paths = etc_paths or []
        self.copy_only = copy_only

    def setup(self, old_version):
        """Create symlinks or copies of files during app update.

        During the transition from shipped configs to the symlink/copy
        approach, files in /etc will be removed during .deb upgrade. This
        method ensures that symlinks or copies are properly recreated.
        """
        if self.app_id and self.app.is_enabled():
            self.enable()

    def enable(self):
        """Create a symlink or copy in /etc/ of the configuration file."""
        for path in self.etc_paths:
            if not privileged.dropin_is_valid(
                    self.app_id, path, self.copy_only, unlink_invalid=True):
                privileged.dropin_link(self.app_id, path, self.copy_only)

    def disable(self):
        """Remove the links/copies in /etc/ of the configuration files."""
        for path in self.etc_paths:
            privileged.dropin_unlink(self.app_id, path, missing_ok=True)

    def diagnose(self) -> list[DiagnosticCheck]:
        """Check all links/copies and return generate diagnostic results."""
        results = []
        for path in self.etc_paths:
            result = privileged.dropin_is_valid(self.app_id, path,
                                                self.copy_only)

            etc_path = self.get_etc_path(path)
            check_id = f'dropin-config-{etc_path}'
            result_string = Result.PASSED if result else Result.FAILED
            description = gettext_noop(
                'Static configuration {etc_path} is setup properly')
            parameters: DiagnosticCheckParameters = {'etc_path': str(etc_path)}
            results.append(
                DiagnosticCheck(check_id, description, result_string,
                                parameters, self.component_id))

        return results

    def get_target_path(self, path):
        """Return Path object for a target path."""
        target = pathlib.Path(self.ROOT)
        target /= self.DROPIN_CONFIG_ROOT.lstrip('/')
        return target / path.lstrip('/')

    def get_etc_path(self, path):
        """Return Path object for etc path."""
        return pathlib.Path(self.ROOT) / path.lstrip('/')
