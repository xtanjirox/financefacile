# Generated by Django 5.0.6 on 2025-05-12 18:34

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0051_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 5, 12, 18, 34, 23, 908948, tzinfo=datetime.timezone.utc)),
        ),
    ]
