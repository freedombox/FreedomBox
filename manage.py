# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Dummy file to help pytest-django path detection.

pytest-django searches for a folder with manage.py and treats that as parent
directory for Django project. This folder is then added to Python path managed
in sys.path. This allows the Django setting module to be discovered as
plinth.tests.data.django_test_settings. pytest can then be invoked simply as
'py.test-3' instead of 'python3 -m pytest'.
"""
