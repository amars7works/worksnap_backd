# Generated by Django 2.1 on 2019-05-22 20:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0013_totalleaves'),
    ]

    operations = [
        migrations.RenameField(
            model_name='userdailyreport',
            old_name='cretaed_at',
            new_name='created_at',
        ),
    ]
