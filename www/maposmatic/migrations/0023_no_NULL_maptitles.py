# Generated by Django 2.2.12 on 2022-03-15 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0022_add_reverse_name_for_uplodas'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maprenderingjob',
            name='maptitle',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]