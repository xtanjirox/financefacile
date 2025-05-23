# Generated by Django 5.0.6 on 2025-04-26 10:42

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_product_created_at_alter_financeentry_entry_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='financeentry',
            name='entry_date',
            field=models.DateField(default=datetime.datetime(2025, 4, 26, 10, 42, 24, 741526, tzinfo=datetime.timezone.utc)),
        ),
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='core.productcategory')),
            ],
            options={
                'verbose_name': 'Product Category',
                'verbose_name_plural': 'Product Categories',
            },
        ),
        migrations.AddField(
            model_name='product',
            name='category',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.PROTECT, related_name='products', to='core.productcategory'),
            preserve_default=False,
        ),
    ]
