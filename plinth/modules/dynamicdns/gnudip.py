# SPDX-License-Identifier: AGPL-3.0-or-later
"""
GnuDIP client for updating Dynamic DNS records.
"""

import hashlib
import logging
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


def update(server: str, domain: str, username: str,
           password: str) -> tuple[bool, str | None]:
    """Update Dynamic DNS record using GnuDIP protocol.

    Protocol documentation:
    https://gnudip2.sourceforge.net/gnudip-www/latest/gnudip/html/protocol.html
    """
    domain = domain.removeprefix(username + '.')
    password_digest = hashlib.md5(password.encode()).hexdigest()

    http_server = f'https://{server}/gnudip/cgi-bin/gdipupdt.cgi'
    response = requests.get(http_server)

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
    update_response = requests.get(http_server, params=query_params)

    update_result = _extract_content_from_meta_tags(update_response.text)
    _check_required_keys(update_result, ['retc'])
    result = (int(update_result['retc']) == 0)
    return result, update_result.get('addr')
