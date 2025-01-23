class SocketMessage:
    def __init__(self):
        self._messages = {}

    def add_message(self, room_id, room_name,user_id, message):
        if room_id not in self._messages:
            self._messages[room_id] = {
                "room_name": room_name,
                "messages": []
            }
        self._messages[room_id]["messages"].append({
            'user_id': user_id,
            'message': message
        })

    def get_messages(self, room_id):
        return self._messages.get(room_id, {"room_name": "", "messages": []})

    def clear_room_messages(self, room_id):
        if room_id in self._messages:
            self._messages[room_id]["messages"].clear()

socket_message_manager = SocketMessage()