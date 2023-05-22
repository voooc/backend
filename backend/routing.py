import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from backend.utils.websocket import TokenAuthMiddleware
from user.consumers import NotificationConsumer

django.setup()
application = ProtocolTypeRouter({
    'websocket': TokenAuthMiddleware(
        URLRouter([
            re_path(r'msg', NotificationConsumer),
        ])
    )
})