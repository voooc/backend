from .base import *
DEBUG = False
HOST = 'http://120.48.97.87/#/'
ALLOWED_HOSTS = ['120.48.97.87']
BROKER_URL = 'redis://120.48.97.87:6379/6'
# BACKEND配置，这里使用redis
CELERY_RESULT_BACKEND = 'redis://120.48.97.87:6379/6'
