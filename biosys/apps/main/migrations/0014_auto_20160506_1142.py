# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-06 03:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0013_auto_20160429_1208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='site',
            name='slope',
            field=models.FloatField(blank=True, help_text='Degrees (0 - 90)', null=True, verbose_name='Slope'),
        ),
    ]
