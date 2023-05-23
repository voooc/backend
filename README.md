# 数据库迁移
python manage.py makemigrations 
python manage.py migrate
#异步器启动
celery -A backend worker -l info -P eventlet
# 设置环境
set ENVIRONMENT=development