#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def main():
    # 检查环境变量
    env = os.getenv('ENVIRONMENT')
    if env == 'dev':
        # 加载开发环境的设置文件
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.dev')
    else:
        # 加载生产环境的设置文件
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings.pro')

    # 其他初始化操作
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
