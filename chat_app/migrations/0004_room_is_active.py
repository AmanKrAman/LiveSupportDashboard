# Generated by Django 4.2.13 on 2025-01-25 15:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat_app', '0003_roomusers_data_of_creation'),
    ]

    operations = [
        migrations.AddField(
            model_name='room',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
