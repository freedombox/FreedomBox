from unittest.mock import Mock, patch

import pytest

from plinth.modules.dynamicdns import gnudip

response_to_salt_request = """
<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=utf8">
    <title>
        GnuDIP Update Server
    </title>
    <meta name="salt" content="gqEuCQYQWD">
    <meta name="time" content="1746978203">
    <meta name="sign" content="3d3b1c8ce32db470c6fd79a76f8dafb5">
</head>
<body></body>
</html>
"""

response_to_update_request = """
<html>
<head>
    <title>
        GnuDIP Update Server
    </title>
    <meta name="retc" content="0">
    <meta name="addr" content="24.81.172.128">
</head>
<body></body>
</html>
"""


def test_parse_meta_tags():
    """Test parsing meta tags from HTML content."""
    expected = {
        'salt': 'gqEuCQYQWD',
        'time': '1746978203',
        'sign': '3d3b1c8ce32db470c6fd79a76f8dafb5'
    }
    actual = gnudip._extract_content_from_meta_tags(response_to_salt_request)
    assert actual == expected


def test_check_required_keys_missing():
    """Test check_required_keys raises ValueError if key missing."""
    data = {'foo': 'bar'}
    with pytest.raises(ValueError) as excinfo:
        gnudip._check_required_keys(data, ['foo', 'baz'])

    assert "Missing required keys" in str(excinfo.value)


def test_check_required_keys_present():
    """Test check_required_keys with all keys present does not raise."""
    data = {'foo': 'bar', 'baz': 'qux'}
    gnudip._check_required_keys(data, ['foo', 'baz'])


def test_update_success():
    """Test GNU DIP update mechanism with HTTP protocol."""
    salt_resp = Mock()
    salt_resp.text = response_to_salt_request
    update_resp = Mock()
    update_resp.text = response_to_update_request

    with patch("plinth.modules.dynamicdns.gnudip.requests.get",
               side_effect=[salt_resp, update_resp]) as mock_get:
        result, addr = gnudip.update(server="http://www.2mbit.com:80",
                                     domain="gnudip.dyn.mpis.net",
                                     username="gnudip", password="password")
        assert result
        assert addr == "24.81.172.128"
        assert mock_get.call_count == 2
