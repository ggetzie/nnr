# Generated by Django 3.0.1 on 2020-03-06 02:27

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import main.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('recipes', '0003_auto_20200224_0508'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaymentPlan',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=25, verbose_name='Name')),
                ('name_slug', models.SlugField(max_length=25, unique=True, verbose_name='Name Slug')),
                ('interval', models.PositiveSmallIntegerField(default=365, verbose_name='Days between payments')),
                ('amount', models.PositiveSmallIntegerField(default=10, verbose_name='Amount')),
                ('stripe_id', models.CharField(default='', max_length=50, verbose_name='Stripe Plan Id')),
            ],
            options={
                'ordering': ['name_slug'],
            },
        ),
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('next_payment', models.DateField(default=main.models.next_year, verbose_name='Next Payment')),
                ('stripe_id', models.CharField(default='', max_length=50, verbose_name='Stripe Customer Id')),
                ('payment_status', models.PositiveSmallIntegerField(choices=[(0, 'FAILED'), (1, 'NEEDS CONFIRMATION'), (2, 'TRIAL'), (3, 'SUCCESS')], default=2, verbose_name='Payment Status')),
                ('subscription_end', models.DateField(verbose_name='Subscription End')),
                ('rate_level', models.PositiveSmallIntegerField(default=1, verbose_name='Rate Level')),
                ('last_sub', models.DateTimeField(default=datetime.datetime(1970, 1, 1, 0, 0, tzinfo=utc), verbose_name='Last Submission')),
                ('plan', models.ForeignKey(default=main.models.get_basic_plan, on_delete=django.db.models.deletion.SET_DEFAULT, to='main.PaymentPlan')),
                ('saved_recipes', models.ManyToManyField(related_name='saved_by', to='recipes.Recipe')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
