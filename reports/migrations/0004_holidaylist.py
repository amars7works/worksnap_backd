# Generated by Django 2.1 on 2018-08-31 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0003_auto_20180829_0719'),
    ]

    operations = [
        migrations.CreateModel(
            name='HolidayList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('holiday_date', models.DateField()),
                ('day', models.CharField(max_length=20)),
                ('holiday_description', models.TextField(null=True)),
            ],
        ),
    ]
