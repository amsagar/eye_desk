# Generated by Django 5.0.4 on 2024-04-12 20:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Backend', '0002_remove_screenshotmodel_activity'),
    ]

    operations = [
        migrations.AlterField(
            model_name='clientmodel',
            name='salary',
            field=models.FloatField(max_length=255),
        ),
    ]
