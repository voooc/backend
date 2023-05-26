"""
WSGI config for backend project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

env = os.getenv('ENVIRONMENT')
if env == 'production':
    # 加载生产环境的设置文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.pro')
else:
    # 加载开发环境的设置文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')

application = get_wsgi_application()
