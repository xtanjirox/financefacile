# Generated by Django 5.0.6 on 2025-05-06 18:46

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0041_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 5, 6, 18, 46, 39, 996614, tzinfo=datetime.timezone.utc)),
        ),
    ]
