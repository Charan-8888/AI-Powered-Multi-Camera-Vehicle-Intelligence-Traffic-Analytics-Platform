from .settings import *

# Tests must be reproducible without local PostgreSQL credentials.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
