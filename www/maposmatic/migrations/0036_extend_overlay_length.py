# Generated by Django 4.2.14 on 2024-07-28 09:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0035_update_keep_until_legacy'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maprenderingjob',
            name='overlay',
            field=models.CharField(blank=True, max_length=4095, null=True),
        ),
    ]
