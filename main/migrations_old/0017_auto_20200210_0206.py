# Generated by Django 3.0.1 on 2020-02-10 02:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
        ('main', '0016_auto_20191222_2333'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='saved_recipes',
            field=models.ManyToManyField(related_name='saved_by', to='recipes.Recipe'),
        ),
    ]
