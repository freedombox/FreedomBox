# Django settings for test modules.

import os
TEST_DATA_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(TEST_DATA_DIR, 'plinth.sqlite3'),
    }
}

DEFAULT_INDEX_TABLESPACE = ''

INSTALLED_APPS = (
    'plinth',
)

# These are included here solely to suppress Django warnings
# during testing setup
MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'plinth.urls'

SECRET_KEY = 'django_tests_secret_key'
