# Generated by Django 2.1 on 2018-08-31 14:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0004_holidaylist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userssummaryreport',
            name='date',
            field=models.DateField(),
        ),
    ]
