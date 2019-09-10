# Generated by Django 1.11.16 on 2019-06-17 16:38

from django.db import migrations

from corehq.sql_db.operations import RawSQLMigration


migrator = RawSQLMigration(('custom', 'icds_reports', 'migrations', 'sql_templates', 'database_views'))


class Migration(migrations.Migration):

    dependencies = [
        ('icds_reports', '0130_thr_mother_column_agg_awc'),
    ]

    operations = [migrator.get_migration('thr_report_view.sql')]
