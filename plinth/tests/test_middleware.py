# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Test module for custom middleware.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest
from django.contrib.auth.models import AnonymousUser, Group, User
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test.client import RequestFactory
from stronghold.decorators import public

from plinth import app as app_module
from plinth.middleware import AdminRequiredMiddleware, SetupMiddleware

setup_helper = None


@pytest.fixture(name='kwargs')
def fixture_kwargs():
    """Fixture for returning kwargs for creating middleware."""
    return {
        'view_func': HttpResponse,
        'view_args': [],
        'view_kwargs': {},
    }


@pytest.fixture(name='app')
def fixture_app():
    """Fixture for returning a test app."""

    class AppTest(app_module.App):
        """Test app."""
        app_id = 'mockapp'

        def __init__(self):
            """Add info component."""
            super().__init__()
            self.add(app_module.Info('mockapp', version=1))

        def get_setup_state(self):
            return app_module.App.SetupState.NEEDS_SETUP

    app_module.App._all_apps = {}
    return AppTest()


class TestSetupMiddleware:
    """Test cases for setup middleware."""

    @staticmethod
    @pytest.fixture(name='middleware')
    def fixture_middleware(load_cfg):
        """Fixture for returning middleware."""
        return SetupMiddleware(True)

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
    @patch('plinth.tests.test_middleware.setup_helper')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    def test_module_is_up_to_date(_reverse, resolve, setup_helper_, app,
                                  middleware, kwargs):
        """Test that none is returned when module is up-to-date."""
        resolve.return_value.namespaces = ['mockapp']
        setup_helper_.is_finished = None
        app.get_setup_state = lambda: app_module.App.SetupState.UP_TO_DATE

        request = RequestFactory().get('/plinth/mockapp')
        request.user = AnonymousUser()
        response = middleware.process_view(request, **kwargs)
        assert response is None

    @staticmethod
    @patch('plinth.tests.test_middleware.setup_helper')
    @patch('plinth.views.SetupView')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    @pytest.mark.django_db
    def test_module_view(_reverse, resolve, setup_view, setup_helper, app,
                         middleware, kwargs):
        """Test that only registered users can access the setup view."""
        resolve.return_value.namespaces = ['mockapp']
        view = Mock()
        setup_view.as_view.return_value = view
        request = RequestFactory().get('/plinth/mockapp')
        request.session = MagicMock()
        setup_helper.is_finished = None

        # Verify that anonymous users cannot access the setup page
        request.user = AnonymousUser()
        with pytest.raises(PermissionDenied):
            middleware.process_view(request, **kwargs)

        setup_view.as_view.assert_not_called()
        view.assert_not_called()

        # Verify that non-admin logged-in users can't access the setup page
        user = User(username='johndoe')
        user.save()
        request.user = user
        with pytest.raises(PermissionDenied):
            middleware.process_view(request, **kwargs)

        setup_view.as_view.assert_not_called()
        view.assert_not_called()

        # Verify that admin logged-in users can access the setup page
        user = User(username='adminuser')
        user.save()
        group = Group(name='admin')
        group.save()
        user.groups.add(group)
        user.save()
        request.user = user
        middleware.process_view(request, **kwargs)
        setup_view.as_view.assert_called_once_with()
        view.assert_called_once_with(request, app_id='mockapp')

    @staticmethod
    @patch('plinth.tests.test_middleware.setup_helper')
    @patch('django.contrib.messages.success')
    @patch('django.urls.resolve')
    @patch('django.urls.reverse', return_value='users:login')
    @pytest.mark.django_db
    def test_install_result_collection(reverse, resolve, messages_success,
                                       setup_helper_, app, middleware, kwargs):
        """Test that module installation result is collected properly."""
        resolve.return_value.namespaces = ['mockapp']
        setup_helper_.is_finished = True
        setup_helper_.collect_result.return_value = None
        app.get_setup_state = lambda: app_module.App.SetupState.UP_TO_DATE

        # Admin user can't collect result
        request = RequestFactory().get('/plinth/mockapp')
        user = User(username='adminuser')
        user.save()
        group = Group(name='admin')
        group.save()
        user.groups.add(group)
        user.save()
        request.user = user
        request.session = MagicMock()
        response = middleware.process_view(request, **kwargs)

        assert response is None
        assert messages_success.called
        setup_helper_.collect_result.assert_called_once_with()

        # Non-admin user can't collect result
        messages_success.reset_mock()
        setup_helper_.collect_result.reset_mock()
        request = RequestFactory().get('/plinth/mockapp')
        user = User(username='johndoe')
        user.save()
        request.user = user
        request.session = MagicMock()
        response = middleware.process_view(request, **kwargs)

        assert response is None
        assert not messages_success.called
        setup_helper_.collect_result.assert_not_called()


class TestAdminMiddleware:
    """Test cases for admin middleware."""

    @staticmethod
    @pytest.fixture(name='middleware')
    def fixture_middleware(load_cfg):
        """Fixture for returning middleware."""
        return AdminRequiredMiddleware(True)

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
    def test_that_public_view_is_allowed_for_normal_user(
            web_request, middleware, kwargs):
        """Test that normal user is allowed for an public view"""
        kwargs = dict(kwargs)
        kwargs['view_func'] = public(HttpResponse)

        response = middleware.process_view(web_request, **kwargs)
        assert response is None
