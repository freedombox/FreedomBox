# SPDX-License-Identifier: AGPL-3.0-or-later
"""Configure Names App."""

import pathlib

from plinth import action_utils
from plinth.actions import privileged

fallback_conf = pathlib.Path(
    '/etc/systemd/resolved.conf.d/freedombox-fallback.conf')
source_fallback_conf = pathlib.Path(
    '/usr/share/freedombox'
    '/etc/systemd/resolved.conf.d/freedombox-fallback.conf')


@privileged
def set_resolved_configuration(dns_fallback: bool | None = None):
    """Set systemd-resolved configuration options."""
    if dns_fallback is not None:
        _set_enable_dns_fallback(dns_fallback)


def get_resolved_configuration() -> dict[str, bool]:
    """Return systemd-resolved configuration."""
    return {'dns_fallback': fallback_conf.exists()}


def _set_enable_dns_fallback(dns_fallback: bool):
    """Update whether to use DNS fallback servers."""
    if dns_fallback:
        if not fallback_conf.exists():
            fallback_conf.parent.mkdir(parents=True, exist_ok=True)
            fallback_conf.symlink_to(source_fallback_conf)
    else:
        fallback_conf.unlink(missing_ok=True)

    action_utils.service_reload('systemd-resolved')
