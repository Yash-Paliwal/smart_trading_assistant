# Generated by Django 4.2.23 on 2025-07-04 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trading_app', '0007_instrument_average_volume'),
    ]

    operations = [
        migrations.AddField(
            model_name='instrument',
            name='sector',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
