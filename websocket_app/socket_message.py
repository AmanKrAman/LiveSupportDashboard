import time
from threading import Lock

class SocketMessage:
    def __init__(self, max_messages_per_room=100):
        self._messages = {}
        self._lock = Lock()  
        self.max_messages_per_room = max_messages_per_room  

    def add_message(self, room_id, room_name, user_id, message):
        with self._lock:  
            if room_id not in self._messages:
                self._messages[room_id] = {
                    "room_name": room_name,
                    "messages": []
                }

            timestamp = time.time()
            self._messages[room_id]["messages"].append({
                'user_id': user_id,
                'message': message,
                'timestamp': timestamp
            })

            if len(self._messages[room_id]["messages"]) > self.max_messages_per_room:
                self._messages[room_id]["messages"].pop(0)  

    def get_messages(self, room_id):
        with self._lock:  
            room_data = self._messages.get(room_id, {"room_name": "", "messages": []})
            room_data["messages"] = sorted(room_data["messages"], key=lambda x: x['timestamp'])
            return room_data

    def clear_room_messages(self, room_id):
        with self._lock:  
            if room_id in self._messages:
                self._messages[room_id]["messages"].clear()

    def get_all_rooms(self):
        with self._lock: 
            return list(self._messages.keys())

socket_message_manager = SocketMessage(max_messages_per_room=100)