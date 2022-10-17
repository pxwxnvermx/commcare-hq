# Generated by Django 3.2.15 on 2022-09-30 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('domain', '0014_appreleasemodesetting'),
    ]

    operations = [
        migrations.AddField(
            model_name='appreleasemodesetting',
            name='is_visible',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='appreleasemodesetting',
            name='domain',
            field=models.CharField(db_index=True, max_length=256, unique=True),
        ),
    ]