"""
WSGI config for tale project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.1/howto/deployment/wsgi/
"""

import os, sys

from django.core.wsgi import get_wsgi_application

sys.path.append('/home/ubuntu/tale/tale')
sys.path.append('/home/ubuntu/tale')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tale.settings')

application = get_wsgi_application()
