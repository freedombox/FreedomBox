# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for utilities.
"""

import tempfile
from unittest.mock import MagicMock, Mock

import pytest
import ruamel.yaml
from django.test.client import RequestFactory
from ruamel.yaml.compat import StringIO

from plinth.utils import YAMLFile, is_user_admin, is_valid_user_name


def test_is_valid_user_name():
    """Test valid user names in Debian."""
    f = is_valid_user_name
    assert not f('this_user_name_is_too_long_to_be_valid')
    assert not f('-invalid')
    assert not f('not\tvalid')
    assert not f('not\nvalid')
    assert not f('not valid')
    assert not f('not:valid')
    assert not f('not/valid')
    assert not f('not\\valid')
    assert f('€.;#@|')


class TestIsAdminUser:
    """Test class for is_user_admin utility."""

    @staticmethod
    @pytest.fixture(name='web_request')
    def fixture_web_request():
        """Setup each test case before execution."""
        web_request = RequestFactory().get('/plinth/mockapp')
        web_request.user = Mock()
        web_request.session = MagicMock()
        return web_request

    @staticmethod
    def test_is_false_for_anonymous_user(web_request):
        """Test anonymous user is reported as non-admin."""
        web_request.user = Mock()
        web_request.user.is_authenticated = False
        assert not is_user_admin(web_request)
        assert not is_user_admin(web_request, cached=True)

    @staticmethod
    def test_values_for_authenticated_users(web_request):
        """Test correct return values for authenticated users."""
        web_request.user.groups.filter().exists = Mock(return_value=False)
        assert not is_user_admin(web_request)
        web_request.user.groups.filter().exists = Mock(return_value=True)
        assert is_user_admin(web_request)

    @staticmethod
    def test_caching_of_values(web_request):
        """Test that caching of values for authenticate users."""
        session_mock = MagicMock()
        session_dict = {}
        session_mock.__setitem__.side_effect = session_dict.__setitem__
        session_mock.__getitem__.side_effect = session_dict.__getitem__
        session_mock.__contains__.side_effect = session_dict.__contains__
        web_request.session = session_mock

        mock = Mock(return_value=False)
        web_request.user.groups.filter().exists = mock
        assert not is_user_admin(web_request)
        mock.assert_called_once_with()
        session_mock.__setitem__.assert_called_once_with(
            'cache_user_is_admin', False)

        mock = Mock(return_value=False)
        web_request.user.groups.filter().exists = mock
        assert not is_user_admin(web_request, cached=True)
        mock.assert_not_called()
        session_mock.__getitem__.assert_called_once_with('cache_user_is_admin')

        mock = Mock(return_value=False)
        web_request.user.groups.filter().exists = mock
        assert not is_user_admin(web_request, cached=False)
        mock.assert_called_once_with()
        session_mock.__getitem__.assert_called_once_with('cache_user_is_admin')


class TestYAMLFileUtil:
    """Check updating YAML files"""

    kv_pair = {'key': 'value'}

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True  # type: ignore [assignment]

    def test_update_empty_yaml_file(self):
        """
        Update an empty YAML file with content.
        """
        test_file = tempfile.NamedTemporaryFile()
        conf = {'property1': self.kv_pair}

        with YAMLFile(test_file.name) as file_conf:
            for key in conf:
                file_conf[key] = conf[key]

        with open(test_file.name, 'r', encoding='utf-8') as retrieved_conf:
            buffer = StringIO()
            self.yaml.dump(conf, buffer)
            assert retrieved_conf.read() == buffer.getvalue()

    def test_update_non_empty_yaml_file(self):
        """
        Update a non-empty YAML file with modifications
        """
        test_file = tempfile.NamedTemporaryFile()

        with open(test_file.name, 'w', encoding='utf-8') as conf_file:
            self.yaml.dump({'property1': self.kv_pair}, conf_file)

        with YAMLFile(test_file.name) as file_conf:
            file_conf['property2'] = self.kv_pair

        with open(test_file.name, 'r', encoding='utf-8') as retrieved_conf:
            file_conf = self.yaml.load(retrieved_conf)
            assert file_conf == {
                'property1': self.kv_pair,
                'property2': self.kv_pair
            }

    @staticmethod
    def test_context_exception():
        """Test that exception during update does not update file."""
        test_file = tempfile.NamedTemporaryFile()
        with pytest.raises(ValueError):
            with YAMLFile(test_file.name) as yaml_file:
                yaml_file['property1'] = 'value1'
                raise ValueError('Test')

        assert open(test_file.name, 'r', encoding='utf-8').read() == ''
