# -*- coding: utf-8 -*-
# Generated by Django 1.11.13 on 2018-07-04 10:08
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0015_auto_20180627_1802'),
    ]

    operations = [
        migrations.RenameField(
            model_name='record',
            old_name='consumed',
            new_name='locked',
        ),
        migrations.RenameField(
            model_name='record',
            old_name='published',
            new_name='validated',
        ),
    ]
