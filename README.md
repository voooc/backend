# 数据库迁移
python manage.py makemigrations 
python manage.py migrate
#异步器启动
source venv/bin/activate
celery -A backend worker -l info -P eventlet
nohup celery -A backend worker -P gevent -c 1000 >celery.log 2>&1 &
# 设置环境
set ENVIRONMENT=development
# 加载uwsgi
lsof -i:8000
kill - 9
service mysql restart
uwsgi --ini /home/project/uwsgi/lab.ini
# nginx
ps -ef|grep nginx
sudo /usr/local/nginx/sbin/nginx -s stop
/usr/local/nginx/sbin/nginx
# 启动elastisearch
/usr/local/elasticsearch-8.7.0/bin/elasticsearch -d