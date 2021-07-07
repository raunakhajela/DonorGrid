# Generated by Django 3.2.5 on 2021-07-07 03:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('Configuration', '0002_auto_20210702_2224'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethod',
            name='environment',
            field=models.CharField(blank=True, choices=[('d', 'Development'), ('p', 'Production')], default='d', help_text='Required for PayPal', max_length=1),
        ),
    ]
