# Generated by Django 3.2.5 on 2021-07-08 04:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Configuration', '0004_alter_paymentmethod_environment'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethod',
            name='is_active',
            field=models.BooleanField(blank=True, default=False),
        ),
    ]
