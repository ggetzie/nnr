# Generated by Django 3.0.7 on 2020-07-01 12:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_auto_20200425_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='approved',
            field=models.BooleanField(default=False, verbose_name='Approved'),
        ),
    ]
