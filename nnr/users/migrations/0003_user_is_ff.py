# Generated by Django 3.1.13 on 2021-10-20 13:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20210810_0138'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_ff',
            field=models.BooleanField(default=False, verbose_name='Friends & Family'),
        ),
    ]
