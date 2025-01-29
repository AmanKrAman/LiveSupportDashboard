from django.db import models
from django.db.models import Index
from django.utils import timezone
class Room(models.Model):
    room_id = models.CharField(max_length=10, primary_key=True)  
    room_name = models.CharField(max_length=60)  
    room_created_by = models.CharField(max_length=10)  
    room_created_on = models.DateTimeField(auto_now_add=True) 
    is_active = models.BooleanField(default=False)   

    class Meta:
        db_table = 'room'
        indexes = [
            Index(fields=['room_created_on']),  
        ]

    def __str__(self):
        return self.room_name

class RoomUsers(models.Model):
    fk_room_id = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='users') 
    user_id = models.CharField(max_length=10)  
    is_active = models.BooleanField(default=False)  
    user_name = models.CharField(max_length=30)  
    position = models.CharField(max_length=10)  
    data_of_creation = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        db_table = 'room_users'
        unique_together = ['fk_room_id', 'user_name']  

    def __str__(self):
        return f"{self.user_name} ({self.position})"

