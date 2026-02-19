# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Quassel."""

import pathlib

from plinth.actions import privileged


@privileged
def set_domain(domain_name: str):
    """Write a file containing domain name."""
    domain_file = pathlib.Path('/var/lib/quassel/domain-freedombox')
    domain_file.write_text(domain_name, encoding='utf-8')
    # Ensure that that file is readable by non-privileged process.
    domain_file.chmod(0o644)
