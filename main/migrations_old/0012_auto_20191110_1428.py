# Generated by Django 2.2.4 on 2019-11-10 14:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0011_auto_20191023_1111'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentplan',
            name='stripe_id',
            field=models.CharField(default='', max_length=50, verbose_name='Stripe Plan Id'),
        ),
        migrations.AddField(
            model_name='profile',
            name='stripe_id',
            field=models.CharField(default='', max_length=50, verbose_name='Stripe Customer Id'),
        ),
    ]
