from confluent_kafka import Consumer, KafkaError
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import threading
from collections import defaultdict

class ChatKafkaConsumer:
    _instance = None
    _lock = threading.Lock()
    _room_messages = defaultdict(list) 
    _MAX_MESSAGES = 50
    _active_rooms = set()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.consumers = {}
                    cls._instance.channel_layer = get_channel_layer()
        return cls._instance

    def create_consumer(self, room_id):
        consumer = Consumer({
            'bootstrap.servers': 'localhost:9092',
            'group.id': f'chat_consumer_group_{room_id}',
            'auto.offset.reset': 'latest',
            'session.timeout.ms': 6000,
            'heartbeat.interval.ms': 2000
        })
        return consumer

    def start_consuming(self, room_id):
        if room_id not in self.consumers:
            consumer = self.create_consumer(room_id)
            consumer.subscribe([f'chat_room_{room_id}'])
            self.consumers[room_id] = consumer

            with self._lock:
                room_name = f"{room_id}__*"
                self._active_rooms.add(room_name)
            
            thread = threading.Thread(
                target=self._consume_messages,
                args=(room_id,),
                daemon=True
            )
            thread.start()

    def _consume_messages(self, room_id):
        consumer = self.consumers[room_id]
        
        try:
            while True:
                msg = consumer.poll(1.0)
                
                if msg is None:
                    continue
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        print(f'Error: {msg.error()}')
                        break
                
                data = json.loads(msg.value())
                self.forward_to_websocket(data)
        
        except Exception as e:
            print(f"Error in consumer thread for room {room_id}: {e}")
        finally:
            consumer.close()
            with self._lock:
                del self.consumers[room_id]

    def forward_to_websocket(self, data):
        
        room_name = f"{data['room_id']}__{data['room_name']}"
        with self._lock:
            room_messages = self._room_messages[room_name]
            room_messages.append(data)
            
            if len(room_messages) > self._MAX_MESSAGES:
                room_messages.pop(0)
        async_to_sync(self.channel_layer.group_send)(
            room_name,
            {
                'type': 'chat_message',
                'room_messages': room_messages
            }
        )

    def clear_room_messages(self, room_id):
        with self._lock:
            room_pattern = f"{room_id}__*"
            self._active_rooms = {
                room for room in self._active_rooms 
                if not room.startswith(room_pattern)
            }
            
            keys_to_remove = [
                key for key in self._room_messages.keys() 
                if key.startswith(f"{room_id}__")
            ]
            for key in keys_to_remove:
                del self._room_messages[key]

    def get_room_messages(self, room_name):
        with self._lock:
            return self._room_messages.get(room_name, [])