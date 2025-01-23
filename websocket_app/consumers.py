import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from chat_app.models import Room, RoomUsers
from .socket_message import socket_message_manager

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.room_id, user_id = self.scope['url_route']['kwargs']['room_user'].split('__')
            self.user_id = user_id 
        except ValueError:
            await self.close()
            return
        
        is_user_in_room = await self.check_user_in_room(self.room_id, user_id)
    
        if not is_user_in_room:
            await self.close()
            return
        
        self.room_name = is_user_in_room.fk_room_id.room_name
        self.room_group_name = self.room_name 
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        socket_message_manager.add_message(
            room_id=self.room_id, 
            room_name=self.room_name,
            user_id=self.user_id, 
            message=message
        )

        room_messages = socket_message_manager.get_messages(self.room_id)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'room_messages': room_messages,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "room_messages": event['room_messages']
        }))

    @database_sync_to_async
    def check_user_in_room(self, room_id, user_id):
        return RoomUsers.objects.filter(
            fk_room_id=room_id,
            user_id=user_id,
            is_active=True
        ).select_related('fk_room_id').first()


