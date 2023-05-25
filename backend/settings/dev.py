from .base import *
DEBUG = True
HOST = 'https://localhost:3000/#/'
ALLOWED_HOSTS = ['*']
BROKER_URL = 'redis://127.0.0.1:6379/6'
# BACKEND配置，这里使用redis
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/6'