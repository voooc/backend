import json
from channels.generic.websocket import AsyncWebsocketConsumer
from user.models import Message
from channels.db import database_sync_to_async


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user:
            await self.close()
        else:
            self.room_name = f'notification_{user.id}'
            await self.channel_layer.group_add(
                self.room_name,
                self.channel_name
            )
            await self.accept()

    async def disconnect(self, close_code):
        user = self.scope['user']
        self.room_name = f'notification_{user.id}'
        await self.channel_layer.group_discard(
            self.room_name,
            self.channel_name
        )

    async def service_message(self, event):
        # 发送信息
        await self.send(event['message'])

    async def receive(self, text_data=None, bytes_data=None):
        data = await self.get_data()
        await self.channel_layer.group_send(
            self.scope['user'].username,
            {
                'type': 'service.message',
                'message': json.dumps(data),
            }
        )

    @database_sync_to_async
    def get_data(self):
        data = {}
        return data