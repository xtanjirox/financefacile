# Generated by Django 5.0.6 on 2025-05-06 18:36

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_product_is_archived_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 5, 6, 18, 36, 31, 183689, tzinfo=datetime.timezone.utc)),
        ),
    ]
