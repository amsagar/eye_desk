# Generated by Django 5.0.4 on 2024-04-12 20:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Backend', '0003_alter_clientmodel_salary'),
    ]

    operations = [
        migrations.AlterField(
            model_name='weeklyactivity',
            name='activityHours',
            field=models.FloatField(default=0.0),
        ),
    ]