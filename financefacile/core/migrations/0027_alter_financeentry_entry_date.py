# Generated by Django 5.0.6 on 2025-04-30 20:32

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 4, 30, 20, 32, 46, 53039, tzinfo=datetime.timezone.utc)),
        ),
    ]
