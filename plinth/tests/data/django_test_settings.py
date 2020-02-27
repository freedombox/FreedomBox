# SPDX-License-Identifier: AGPL-3.0-or-later
"""
Django settings for test modules.
"""

import os

TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__))

AXES_ENABLED = False

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache'
    }
}

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(TEST_DATA_DIR, 'plinth.sqlite3'),
    }
}

INSTALLED_APPS = [
    'axes',
    'captcha',
    'bootstrapform',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'stronghold',
    'plinth',
]

# These are included here solely to suppress Django warnings
# during testing setup
MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'plinth.tests.data.urls'

SECRET_KEY = 'django_tests_secret_key'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'APP_DIRS': True,
    'DIRS': ['plinth/tests/data/templates/'],
}]
