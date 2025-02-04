from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient, NewTopic
from datetime import datetime
import json
import logging
from typing import Optional, Any
import time

logger = logging.getLogger(__name__)

class ChatKafkaProducer:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            kafka_config = {
                'bootstrap.servers': 'localhost:9092',
                'client.id': 'websocket_chat_producer',
                'acks': 'all',
                'retries': 3,
                'retry.backoff.ms': 1000
            }
            cls._instance.producer = Producer(kafka_config)
            cls._instance.admin_client = AdminClient(kafka_config)
        return cls._instance
    
    def create_topic_if_not_exists(self, topic_name: str) -> bool:
        try:
            metadata = self.admin_client.list_topics(timeout=5)
            if topic_name in metadata.topics:
                return True

            topic = NewTopic(
                topic_name,
                num_partitions=1,
                replication_factor=1
            )
            
            futures = self.admin_client.create_topics([topic])
            
            for topic, future in futures.items():
                try:
                    future.result(timeout=5)  
                    logger.info(f"Topic {topic} created successfully")
                    return True
                except Exception as e:
                    logger.error(f"Failed to create topic {topic}: {e}")
                    return False

        except Exception as e:
            logger.error(f"Error creating topic {topic_name}: {e}")
            return False
    

    def send_message(self, type: str, room_id: str, user_id: str, message: str, room_name: str) -> None:
        topic_name = f'chat_room_{room_id}'
            
        if not self.create_topic_if_not_exists(topic_name):
            logger.error(f"Failed to ensure topic exists: {topic_name}")
            return

        data = {
            'type': type,
            'room_id': room_id,
            'user_id': user_id,
            'message': message,
            'room_name': room_name,
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.producer.produce(
                topic=topic_name,
                key=str(user_id),
                value=json.dumps(data),
                callback=self.delivery_callback
            )
            self.producer.flush(timeout=5)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    def delivery_callback(self, err: Optional[Exception], msg: Any) -> None:
        if err:
            logger.error(f'Message delivery failed: {err}')
        else:
            logger.debug(
                f'Message delivered to {msg.topic()} '
                f'[{msg.partition()}] at offset {msg.offset()}'
            )