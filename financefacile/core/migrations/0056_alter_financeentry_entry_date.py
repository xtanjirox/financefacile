# Generated by Django 5.0.6 on 2025-05-12 21:29

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0055_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 5, 12, 21, 29, 17, 194097, tzinfo=datetime.timezone.utc)),
        ),
    ]
