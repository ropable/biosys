# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-13 06:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteVisitDataFileError',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField()),
                ('file', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.SiteVisitDataFile')),
            ],
        ),
    ]
