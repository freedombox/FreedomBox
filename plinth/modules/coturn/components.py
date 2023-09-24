# SPDX-License-Identifier: AGPL-3.0-or-later
"""App component for other apps to manage their STUN/TURN server configuration.
"""

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field
from time import time
from typing import ClassVar, Iterable

from plinth import app

TURN_REST_TTL = 24 * 3600

TURN_REST_USER = 'fbxturnuser'

TURN_URI_REGEX = r'(stun|turn):(.*):([0-9]{4})\?transport=(tcp|udp)'


@dataclass
class TurnConfiguration:
    """Data class to hold TURN server configuration.

    domain is the string representing the domain name with which Coturn has
    been configured. This is necessary to associate the correct TLS certificate
    with Coturn communication. STUN/TURN URIs are generated using this.

    shared_secret is a string that must be used by a server to be accepted by
    Coturn server. This is the value set in Coturn configuration file.

    uris are a list of strings that represent the full set of STUN/TURN URIs
    that must be used by a STUN/TURN client after advice from the server.

    """
    domain: str | None = None
    uris: list[str] = field(default_factory=list)
    shared_secret: str | None = None

    def __post_init__(self):
        """Generate URIs after object initialization if necessary."""
        if self.domain and not self.uris:
            self.uris = [
                f'{typ}:{self.domain}:3478?transport={transport}'
                for typ in ['stun', 'turn'] for transport in ['tcp', 'udp']
            ]

    def to_json(self) -> str:
        """Return a JSON representation of the configuration."""
        return json.dumps({
            'domain': self.domain,
            'uris': self.uris,
            'shared_secret': self.shared_secret
        })

    @staticmethod
    def validate_turn_uris(turn_uris: list[str]) -> bool:
        """Return whether the given TURN URI is valid."""
        pattern = re.compile(TURN_URI_REGEX)
        return all(map(pattern.match, turn_uris))


@dataclass
class UserTurnConfiguration(TurnConfiguration):
    """Data class to hold per-user TURN server configuration.

    username is a string to identify a specific user and is related to
    the credential.

    credential is a string generated for this user that must be used
    by a server to be accepted by Coturn server. It is generated for
    each user separately upon request and will expire after a set
    time.

    """
    username: str | None = None
    credential: str | None = None

    def to_json(self) -> str:
        """Return a JSON representation of the configuration."""
        return json.dumps({
            'domain': self.domain,
            'uris': self.uris,
            'username': self.username,
            'credential': self.credential
        })


class TurnConsumer(app.FollowerComponent):
    """Component to manage coturn configuration.

    In order to provide audio/video calling functionality, communication
    servers very often use an external server such as Coturn for implementing
    the STUN/TURN protocol. To use Coturn, the server needs to be configured
    with a set of URIs provided by Coturn along with a shared secret.

    This component when added to an app allows the app to retrieve the current
    Coturn configuration and respond to any future configuration changes.

    """

    _all: ClassVar[dict[str, 'TurnConsumer']] = {}

    def __init__(self, component_id):
        """Initialize the component.

        component_id should be a unique ID across all components of an app and
        across all components.

        """
        super().__init__(component_id)
        self._all[component_id] = self

    @classmethod
    def list(cls) -> Iterable['TurnConsumer']:
        """Return a list of all Coturn components."""
        return cls._all.values()

    def on_config_change(self, config: TurnConfiguration):
        """Add or update STUN/TURN configuration.

        Override this method and change app's configuration.

        """

    def get_configuration(self) -> TurnConfiguration:
        """Return current coturn configuration."""
        from plinth.modules import coturn
        return coturn.get_config()


class TurnTimeLimitedConsumer(TurnConsumer):
    """Component to manage coturn configuration with time-limited
    credential.

    This component will generate a new credential upon each request,
    which will expire after 1 day. The shared secret is used to
    generate the credential, but is not provided in the configuration.

    """

    def get_configuration(self) -> UserTurnConfiguration:
        """Return user coturn configuration."""
        from plinth.modules import coturn
        static_config = coturn.get_config()
        timestamp = int(time()) + TURN_REST_TTL
        username = str(timestamp) + ':' + TURN_REST_USER
        credential = None
        if static_config.shared_secret:
            digest = hmac.new(bytes(static_config.shared_secret, 'utf-8'),
                              bytes(username, 'utf-8'), hashlib.sha1).digest()
            credential = base64.b64encode(digest).decode()

        return UserTurnConfiguration(static_config.domain, static_config.uris,
                                     None, username, credential)
