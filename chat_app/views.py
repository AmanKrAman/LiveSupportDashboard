from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from rest_framework import status
from django.db.models import Q
from django.db import IntegrityError
from .models import Room , RoomUsers
import uuid , re
from websocket_app.socket_message import socket_message_manager

def generate_unique_id(name):
    cleaned_name = name.replace(" ", "").lower()[:5]  
    unique_part = uuid.uuid4().hex[:5]  
    return f"{cleaned_name}{unique_part}"[:10] 


class CreateRoomView(APIView):
    def post(self , request, *args , **kwargs):

        room_name = request.data.get('room_name')
        user_name = request.data.get('user_name')

        if not room_name or not user_name:
            return Response({"error": "Room name and User name are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        room_id = generate_unique_id(room_name)
        user_id = generate_unique_id(user_name)

        room = Room.objects.create(
            room_id=room_id,
            room_name=room_name,
            room_created_by=user_name,
        )

        room_user = RoomUsers.objects.create(
            fk_room_id=room,
            user_id=user_id,
            is_active=True,
            user_name=user_name,
            position="ADMIN",
        )

        return Response({
            "message": "Room created successfully",
            "room_id": room.room_id,
            "user_id": room_user.user_id
        }, status=status.HTTP_201_CREATED)
    

class GetRoomsView(APIView):
    def post(self ,request, *args , **kwargs):

        input_data = request.data.get('input', '').strip()  

        if input_data:
            if re.match(r'^[A-Za-z0-9]+$', input_data):
                rooms = Room.objects.filter(room_id__icontains=input_data)
            else:
                rooms = Room.objects.filter(room_name__icontains=input_data)
        else:
            rooms = Room.objects.order_by('-room_created_on')[:5]

        room_data = []
        for room in rooms:
            active_users_count = RoomUsers.objects.filter(fk_room_id=room, is_active=True).count()
            room_data.append({
                "room_id": room.room_id,
                "room_name": room.room_name,
                "active_users": active_users_count
            })

        return Response({
            "rooms": room_data
        }, status=status.HTTP_200_OK)

class JoinRoomView(APIView):
    def post(self ,request, *args , **kwargs):

        user_name = request.data.get('user_name', '').strip()
        input_data = request.data.get('room_id_or_name', '').strip() 
        
        if not input_data:
            return Response({"detail": "room_id_or_name must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        room = Room.objects.filter(Q(room_id=input_data) | Q(room_name=input_data)).first()

        if not room:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
        
        existing_user = RoomUsers.objects.filter(fk_room_id=room, user_name=user_name).first()

        if existing_user:
            if existing_user.position == 'ADMIN':
                existing_user.is_active = True
                existing_user.save()  
                response_data = {
                    "detail": "Admin user successfully rejoined the room.",
                    "room_id": room.room_id,
                    "room_name": room.room_name,
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            else:
                return Response({"detail": "User is already a member of the room."}, status=status.HTTP_400_BAD_REQUEST)

        random_name = user_name + room.room_name
        user_id = generate_unique_id(random_name)

        RoomUsers.objects.create(
            fk_room_id=room,
            user_id=user_id,
            user_name=user_name,
            position='MEMBER',
            is_active=True
        )

        active_users_count = RoomUsers.objects.filter(fk_room_id=room, is_active=True).count()

        response_data = {
            "detail": "User successfully joined the room.",
            "user_id": user_id,
            "room_id": room.room_id,
            "room_name": room.room_name,
            "active_users": active_users_count
        }

        return Response(response_data, status=status.HTTP_201_CREATED)



class DisjoinRoomView(APIView):
    def post(self ,request, *args , **kwargs):

        room_id = request.data.get('room_id', '').strip()
        input_data = request.data.get('user_id_or_name', '').strip()

        if not room_id or not input_data:
            return Response({"detail": "room_id and user_id_or_name must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        room = Room.objects.filter(room_id=room_id).first()
        if not room:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)
        
        user = RoomUsers.objects.filter(fk_room_id=room).filter(Q(user_id=input_data) | Q(user_name=input_data)).first()

        if not user:
            return Response({"detail": "User not found in the room."}, status=status.HTTP_404_NOT_FOUND)
        
        if user.position == 'MEMBER':
            user.delete()

            response_data = {
                "detail": "User successfully disjoined the room.",
                "room_id": room.room_id,
                "room_name": room.room_name,
            }
            return Response(response_data, status=status.HTTP_200_OK)
        elif user.position == 'ADMIN':
            RoomUsers.objects.filter(fk_room_id=room, position='MEMBER').delete()

            user.is_active = False
            user.save()

            response_data = {
                "detail": "Admin user has left the room. All other members have been deleted, and admin is deactivated.",
                "room_id": room.room_id,
                "room_name": room.room_name,
            }
            return Response(response_data, status=status.HTTP_200_OK)



class DeleteRoomView(APIView):
    def post(self ,request, *args , **kwargs):

        room_id = request.data.get('room_id', '').strip()
        input_data = request.data.get('user_id_or_name', '').strip()

        if not room_id or not input_data:
            return Response({"detail": "Both room_id and user_id_or_name must be provided."}, status=status.HTTP_400_BAD_REQUEST)

        room = Room.objects.filter(room_id=room_id).first()
        
        if not room:
            return Response({"detail": "Room not found."}, status=status.HTTP_404_NOT_FOUND)

        user = RoomUsers.objects.filter(fk_room_id=room).filter(Q(user_id=input_data) | Q(user_name=input_data)).first()
        
        if not user:
            return Response({"detail": "User not found in the room."}, status=status.HTTP_404_NOT_FOUND)

        if user.position != 'ADMIN':
            return Response({"detail": "Only an admin can delete the room."}, status=status.HTTP_403_FORBIDDEN)
        
        socket_message_manager.clear_room_messages(room.room_id)
        room.delete() 


        return Response({"detail": "Room and its associated users have been deleted successfully."}, status=status.HTTP_200_OK)


