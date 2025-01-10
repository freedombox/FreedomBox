# SPDX-License-Identifier: AGPL-3.0-or-later

from plinth.errors import PlinthError


class BorgError(PlinthError):
    """Generic borg errors"""


class BorgRepositoryDoesNotExistError(BorgError):
    """Borg access to a repository works but the repository does not exist"""


class SshfsError(PlinthError):
    """Generic sshfs errors"""


class BorgRepositoryExists(BorgError):
    """A repository at target location already exists during initialization."""


class BorgUnencryptedRepository(BorgError):
    """Attempt to provide password on an unencrypted repository."""


class BorgArchiveExists(BorgError):
    """A archive with the given name already exists in the repository."""


class BorgArchiveDoesNotExist(BorgError):
    """Specified archive does not exist in the repository."""


class BorgBusy(BorgError):
    """Borg could not acquire lock being busy with another operation."""
