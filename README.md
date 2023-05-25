# 数据库迁移
python manage.py makemigrations 
python manage.py migrate
#异步器启动
source venv/bin/activate
celery -A backend worker -l info -P eventlet
# 设置环境
set ENVIRONMENT=development
# 加载uwsgi
lsof -i:8000
kill - 9
service mysql restart
uwsgi --ini /home/project/uwsgi/lab.ini
# 启动
sudo /usr/local/nginx/sbin/nginx -s stop
# nginx
ps -ef|grep nginx