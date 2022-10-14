# SPDX-License-Identifier: AGPL-3.0-or-later
"""Application manifest for privacy app."""

from . import privileged

backup = {'config': {'files': [str(privileged.CONFIG_FILE)]}}
