# Generated by Django 4.2.11 on 2024-04-10 18:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0002_bill_billitem'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='phone_number',
        ),
        migrations.AddField(
            model_name='customer',
            name='address',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='customer',
            name='phone',
            field=models.CharField(default='', max_length=20),
        ),
    ]
