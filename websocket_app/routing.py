from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/lsd/chat/(?P<room_user>\w+)/$', consumers.ChatConsumer.as_asgi()),
]