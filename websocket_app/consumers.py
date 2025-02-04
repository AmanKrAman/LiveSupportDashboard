import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from asgiref.sync import sync_to_async
from chat_app.models import Room, RoomUsers
from datetime import datetime
from .socket_message import socket_message_manager
from .kafka.producer import ChatKafkaProducer
from .kafka.consumer import ChatKafkaConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.kafka_producer = ChatKafkaProducer()
        self.kafka_consumer = ChatKafkaConsumer()
        self.room_id = None
        self.user_id = None
        self.room_name = None
        self.room_group_name = None

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
        
        self.room_name = self.room_id + '__' + is_user_in_room.fk_room_id.room_name 
        self.room_group_name = self.room_name 

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        self.kafka_consumer.start_consuming(self.room_id)
        await self.accept()

        self.kafka_producer.send_message(
            type = 'user joined',
            room_id=self.room_id,
            user_id=self.user_id,
            message=f'New user joined the team: {self.user_id}',
            room_name=self.room_name.split('__')[1]
        )

    async def disconnect(self, close_code):
        
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        if not message:
            return

        # socket_message_manager.add_message(
        #     room_id=self.room_id, 
        #     room_name=self.room_name,
        #     user_id=self.user_id, 
        #     message=message
        # )

        # room_messages = socket_message_manager.get_messages(self.room_id)

        self.kafka_producer.send_message(
            type= 'message',
            room_id=self.room_id,
            user_id=self.user_id,
            message=message,
            room_name=self.room_name.split('__')[1]
        )

        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'room_messages': room_messages,
        #     }
        # )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "room_messages": event.get('room_messages', [])
        }))

    async def close_room(self, event):
        self.kafka_consumer.clear_room_messages(self.room_id)
        await self.send(text_data=json.dumps({
            "type": "room_closed",
            "detail": event['detail'],
        }))
        await self.close()

    @database_sync_to_async
    def check_user_in_room(self, room_id, user_id):
        return RoomUsers.objects.filter(
            fk_room_id=room_id,
            user_id=user_id,
            is_active=True,
            fk_room_id__is_active = True
        ).select_related('fk_room_id').first()


