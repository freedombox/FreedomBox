#
# This file is part of Plinth.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

"""
Test module for Plinth's custom middleware.
"""

from unittest.mock import Mock, patch

from django.http import HttpResponse
from django.test import TestCase
from django.test.client import RequestFactory

from plinth import cfg
from plinth.middleware import SetupMiddleware


class TestSetupMiddleware(TestCase):
    """Test cases for setup middleware."""
    @classmethod
    def setUpClass(cls):
        """Setup all the test cases."""
        super(TestSetupMiddleware, cls).setUpClass()

        cfg.read()

    def setUp(self):
        """Setup each test case before execution."""
        super(TestSetupMiddleware, self).setUp()

        self.middleware = SetupMiddleware()

        self.kwargs = {
            'view_func': HttpResponse,
            'view_args': [],
            'view_kwargs': {},
        }

    def test_404_urls(self):
        """Test how middleware deals with 404 URLs."""
        request = RequestFactory().get('/plinth/non-existing-url')

        response = self.middleware.process_view(request, **self.kwargs)

        self.assertEqual(response, None)

    def test_url_not_an_application(self):
        """Test that none is returned for URLs that are not applications."""
        request = RequestFactory().get('/plinth/')

        response = self.middleware.process_view(request, **self.kwargs)

        self.assertEqual(response, None)

    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    def test_module_is_up_to_date(self, resolve, loaded_modules):
        """Test that none is returned when module is up-to-date."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.setup_helper.is_finished = None
        module.setup_helper.get_state.return_value = 'up-to-date'
        loaded_modules.__getitem__.return_value = module

        request = RequestFactory().get('/plinth/mockapp')

        response = self.middleware.process_view(request, **self.kwargs)

        self.assertEqual(response, None)

    @patch('plinth.views.SetupView')
    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    def test_module_view(self, resolve, loaded_modules, setup_view):
        """Test that setup view is returned."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.setup_helper.is_finished = None
        loaded_modules.__getitem__.return_value = module
        view = Mock()
        setup_view.as_view.return_value = view

        request = RequestFactory().get('/plinth/mockapp')
        self.middleware.process_view(request, **self.kwargs)

        setup_view.as_view.assert_called_once_with()
        view.assert_called_once_with(request, setup_helper=module.setup_helper)

    @patch('django.contrib.messages.success')
    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    def test_install_result_collection(self, resolve, loaded_modules,
                                       messages_success):
        """Test that module installation result is collected properly."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.setup_helper.is_finished = True
        module.setup_helper.collect_result.return_value = None
        module.setup_helper.get_state.return_value = 'up-to-date'
        loaded_modules.__getitem__.return_value = module

        request = RequestFactory().get('/plinth/mockapp')
        response = self.middleware.process_view(request, **self.kwargs)

        self.assertIsNone(response)
        assert messages_success.called
        module.setup_helper.collect_result.assert_called_once_with()
