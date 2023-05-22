# 数据库迁移
python manage.py makemigrations
python manage.py migrate

celery -A backend worker -l info -P eventlet
