# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom middleware.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test.client import RequestFactory
from stronghold.decorators import public

from plinth.middleware import AdminRequiredMiddleware, SetupMiddleware


@pytest.fixture(name='kwargs')
def fixture_kwargs():
    """Fixture for returning kwargs for creating middleware."""
    return {
        'view_func': HttpResponse,
        'view_args': [],
        'view_kwargs': {},
    }


class TestSetupMiddleware:
    """Test cases for setup middleware."""

    @staticmethod
    @pytest.fixture(name='middleware')
    def fixture_middleware(load_cfg):
        """Fixture for returning middleware."""
        return SetupMiddleware()

    @staticmethod
    @patch('django.urls.reverse', return_value='users:login')
    def test_404_urls(reverse, middleware, kwargs):
        """Test how middleware deals with 404 URLs."""
        request = RequestFactory().get('/plinth/non-existing-url')
        response = middleware.process_view(request, **kwargs)
        assert response is None

    @staticmethod
    @patch('django.urls.reverse', return_value='users:login')
    def test_url_not_an_application(reverse, middleware, kwargs):
        """Test that none is returned for URLs that are not applications."""
        request = RequestFactory().get('/plinth/')
        response = middleware.process_view(request, **kwargs)
        assert response is None

    @staticmethod
    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    def test_module_is_up_to_date(reverse, resolve, loaded_modules, middleware,
                                  kwargs):
        """Test that none is returned when module is up-to-date."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.setup_helper.is_finished = None
        module.setup_helper.get_state.return_value = 'up-to-date'
        loaded_modules.__getitem__.return_value = module

        request = RequestFactory().get('/plinth/mockapp')
        response = middleware.process_view(request, **kwargs)
        assert response is None

    @staticmethod
    @patch('plinth.views.SetupView')
    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    def test_module_view(reverse, resolve, loaded_modules, setup_view,
                         middleware, kwargs):
        """Test that only registered users can access the setup view."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.setup_helper.is_finished = None
        loaded_modules.__getitem__.return_value = module
        view = Mock()
        setup_view.as_view.return_value = view
        request = RequestFactory().get('/plinth/mockapp')

        # Verify that anonymous users cannot access the setup page
        request.user = AnonymousUser()
        middleware.process_view(request, **kwargs)
        setup_view.as_view.assert_called_once_with()
        view.assert_not_called()

        # Verify that logged-in users can access the setup page
        request.user = User(username='johndoe')
        middleware.process_view(request, **kwargs)
        view.assert_called_once_with(request, setup_helper=module.setup_helper)

    @staticmethod
    @patch('django.contrib.messages.success')
    @patch('plinth.module_loader.loaded_modules')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    def test_install_result_collection(reverse, resolve, loaded_modules,
                                       messages_success, middleware, kwargs):
        """Test that module installation result is collected properly."""
        resolve.return_value.namespaces = ['mockapp']
        module = Mock()
        module.is_essential = False
        module.setup_helper.is_finished = True
        module.setup_helper.collect_result.return_value = None
        module.setup_helper.get_state.return_value = 'up-to-date'
        loaded_modules.__getitem__.return_value = module

        request = RequestFactory().get('/plinth/mockapp')
        response = middleware.process_view(request, **kwargs)

        assert response is None
        assert messages_success.called
        module.setup_helper.collect_result.assert_called_once_with()


class TestAdminMiddleware:
    """Test cases for admin middleware."""

    @staticmethod
    @pytest.fixture(name='middleware')
    def fixture_middleware(load_cfg):
        """Fixture for returning middleware."""
        return AdminRequiredMiddleware()

    @staticmethod
    @pytest.fixture(name='web_request')
    def fixture_web_request():
        """Fixture for returning kwargs."""
        web_request = RequestFactory().get('/plinth/mockapp')
        web_request.user = Mock()
        return web_request

    @staticmethod
    def test_that_admin_view_is_denied_for_usual_user(web_request, middleware,
                                                      kwargs):
        """Test that normal user is denied for an admin view"""
        web_request.user.groups.filter().exists = Mock(return_value=False)
        web_request.session = MagicMock()
        with pytest.raises(PermissionDenied):
            middleware.process_view(web_request, **kwargs)

    @staticmethod
    def test_group_view_is_denied_for_non_group_user(web_request, middleware,
                                                     kwargs):
        """Test that group view is allowed for an admin user."""
        web_request.user.groups.filter().exists = Mock(return_value=False)
        web_request.session = MagicMock()
        with patch(
                'plinth.middleware.AdminRequiredMiddleware.check_user_group',
                lambda x, y: False):
            with pytest.raises(PermissionDenied):
                middleware.process_view(web_request, **kwargs)

    @staticmethod
    def test_group_view_is_allowed_for_group_user(web_request, middleware,
                                                  kwargs):
        """Test that group view is allowed for an admin user."""
        web_request.user.groups.filter().exists = Mock(return_value=False)
        web_request.session = MagicMock()
        with patch(
                'plinth.middleware.AdminRequiredMiddleware.check_user_group',
                lambda x, y: True):
            response = middleware.process_view(web_request, **kwargs)
            assert response is None

    @staticmethod
    def test_that_admin_view_is_allowed_for_admin_user(web_request, middleware,
                                                       kwargs):
        """Test that admin user is allowed for an admin view"""
        web_request.user.groups.filter().exists = Mock(return_value=True)
        web_request.session = MagicMock()
        response = middleware.process_view(web_request, **kwargs)
        assert response is None

    @staticmethod
    def test_that_public_view_is_allowed_for_normal_user(web_request,
                                                         middleware, kwargs):
        """Test that normal user is allowed for an public view"""
        kwargs = dict(kwargs)
        kwargs['view_func'] = public(HttpResponse)

        response = middleware.process_view(web_request, **kwargs)
        assert response is None
