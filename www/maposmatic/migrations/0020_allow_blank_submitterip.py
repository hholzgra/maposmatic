# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2020-03-11 15:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('maposmatic', '0019_maprenderingjob_renderstep'),
    ]

    operations = [
        migrations.AlterField(
            model_name='maprenderingjob',
            name='submitterip',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]