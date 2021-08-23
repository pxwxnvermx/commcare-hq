# Generated by Django 2.2.24 on 2021-08-11 12:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('auditcare', '0005_auditcaremigrationmeta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='auditcaremigrationmeta',
            name='modified_at',
        ),
        migrations.AddField(
            model_name='auditcaremigrationmeta',
            name='finished_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AddField(
            model_name='auditcaremigrationmeta',
            name='last_doc_processed',
            field=models.CharField(max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='auditcaremigrationmeta',
            name='other_doc_type_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='auditcaremigrationmeta',
            name='created_at',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='auditcaremigrationmeta',
            name='key',
            field=models.CharField(db_index=True, max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='auditcaremigrationmeta',
            name='record_count',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
