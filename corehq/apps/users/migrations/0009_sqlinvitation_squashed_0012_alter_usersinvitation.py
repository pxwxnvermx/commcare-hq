# Generated by Django 2.2.11 on 2020-04-09 18:53

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    replaces = [('users', '0009_sqlinvitation'), ('users', '0010_populate_usersinvitation'), ('users', '0011_sqlinvitation_uuid'), ('users', '0012_alter_usersinvitation')]

    dependencies = [
        ('users', '0008_auto_20200129_1852'),
    ]

    operations = [
        migrations.CreateModel(
            name='SQLInvitation',
            fields=[
                ('id', models.IntegerField(db_index=True, null=True)),
                ('email', models.CharField(db_index=True, max_length=255)),
                ('invited_by', models.CharField(max_length=126)),
                ('invited_on', models.DateTimeField()),
                ('is_accepted', models.BooleanField(default=False)),
                ('domain', models.CharField(max_length=255)),
                ('role', models.CharField(max_length=100, null=True)),
                ('program', models.CharField(max_length=126, null=True)),
                ('supply_point', models.CharField(max_length=126, null=True)),
                ('couch_id', models.CharField(db_index=True, max_length=126, null=True)),
                ('uuid', models.UUIDField(db_index=True, default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
            options={
                'db_table': 'users_invitation',
            },
        ),
    ]
