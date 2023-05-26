import os
from celery import Celery, platforms

from django.conf import settings
env = os.getenv('ENVIRONMENT')
print(env)
if env == 'production':
    # 加载生产环境的设置文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.pro')
else:
    # 加载开发环境的设置文件
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')

platforms.C_FORCE_ROOT = True  # 加上这一行
# Celery的参数是你当前项目的名称
app = Celery('backend')
# 这一步让你可以在django的settings.py中配置celery
app.config_from_object('django.conf:settings')

# celery会自动在你注册的app中寻找tasks.py，所以你的tasks.py必须放在各个app的目录下并且不能随意命名
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))