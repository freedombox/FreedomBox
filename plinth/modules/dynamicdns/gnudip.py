# SPDX-License-Identifier: AGPL-3.0-or-later
"""
GnuDIP client for updating Dynamic DNS records.
"""

import hashlib
import logging
import socket
from html.parser import HTMLParser

import requests

logger = logging.getLogger(__name__)


class MetaTagParser(HTMLParser):
    """Extracts name and content from HTML meta tags as a dictionary."""

    def __init__(self) -> None:
        """Initialize the meta tags."""
        super().__init__()
        self.meta: dict[str, str] = {}

    def handle_starttag(self, tag: str,
                        attrs: list[tuple[str, str | None]]) -> None:
        """Handle encountering an opening HTML tag during parsing."""
        if tag.lower() == 'meta':
            attr_dict = dict(attrs)
            name = attr_dict.get('name')
            content = attr_dict.get('content')
            if name and content:
                self.meta[name] = content


def _extract_content_from_meta_tags(html: str) -> dict[str, str]:
    """Return a dict of {name: content} for all meta tags in the HTML."""
    parser = MetaTagParser()
    parser.feed(html)
    return parser.meta


def _check_required_keys(dictionary: dict[str, str], keys: list[str]) -> None:
    missing_keys = [key for key in keys if key not in dictionary]
    if missing_keys:
        raise ValueError(
            f"Missing required keys in response: {', '.join(missing_keys)}")


def _request_get_ipv4(*args, **kwargs):
    """Make a IPv4-only request.

    XXX: This monkey-patches socket.getaddrinfo which may causes issues when
    running multiple threads. With urllib3 >= 2.4 (Trixie has 2.3), it is
    possible to implement more cleanly. Use a session for requests library. In
    the session add custom adapter for https:. In the adapter, override
    creation of pool manager, and pass socket_family parameter.
    """
    original = socket.getaddrinfo

    def getaddrinfo_ipv4(*args, **kwargs):
        return original(args[0], args[1], socket.AF_INET, *args[3:], **kwargs)

    socket.getaddrinfo = getaddrinfo_ipv4
    try:
        return requests.get(*args, **kwargs)
    finally:
        socket.getaddrinfo = original


def update(server: str, domain: str, username: str,
           password: str) -> tuple[bool, str | None]:
    """Update Dynamic DNS record using GnuDIP protocol.

    Protocol documentation:
    https://gnudip2.sourceforge.net/gnudip-www/latest/gnudip/html/protocol.html

    GnuDIP at least as deployed on the FreedomBox foundation servers does not
    support IPv6 (it does have any code to update AAAA records). So, make a
    request only using IPv4 stack.
    """
    domain = domain.removeprefix(username + '.')
    password_digest = hashlib.md5(password.encode()).hexdigest()

    http_server = f'https://{server}/gnudip/cgi-bin/gdipupdt.cgi'
    response = _request_get_ipv4(http_server)

    salt_response = _extract_content_from_meta_tags(response.text)
    _check_required_keys(salt_response, ['salt', 'time', 'sign'])

    salt = salt_response['salt']
    password_digest = hashlib.md5(
        f'{password_digest}.{salt}'.encode()).hexdigest()

    query_params = {
        'salt': salt,
        'time': salt_response['time'],
        'sign': salt_response['sign'],
        'user': username,
        'domn': domain,
        'pass': password_digest,
        'reqc': '2'
    }
    update_response = _request_get_ipv4(http_server, params=query_params)

    update_result = _extract_content_from_meta_tags(update_response.text)
    _check_required_keys(update_result, ['retc'])
    result = (int(update_result['retc']) == 0)
    return result, update_result.get('addr')
