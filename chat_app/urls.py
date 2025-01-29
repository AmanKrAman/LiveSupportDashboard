from django.urls import path
from .views import * 

urlpatterns = [
    path('create_room',CreateRoomView.as_view(), name = 'create_room'),
    path('get_rooms',GetRoomsView.as_view(), name = 'get_room'),
    path('join_room',JoinRoomView.as_view(), name = 'join_room'),
    path('disjoin_room',DisjoinRoomView.as_view(), name = 'disjoin_room'),
    path('delete_room',DeleteRoomView.as_view(), name = 'delete_room'),
    path('toggle_room',ToggleRoomView.as_view(), name = 'toggle_room'),
]