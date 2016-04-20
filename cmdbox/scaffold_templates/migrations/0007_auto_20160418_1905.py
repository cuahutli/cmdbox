# -*- coding: utf-8 -*-
# Generated by Django 1.9.4 on 2016-04-18 19:05
from __future__ import unicode_literals

import cmdbox.scaffold_templates.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('scaffold_templates', '0006_auto_20160411_2043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='file_type',
            field=models.PositiveSmallIntegerField(choices=[(1, 'file'), (2, 'folder')], default=1, verbose_name='file type'),
        ),
        migrations.AlterField(
            model_name='file',
            name='folder',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='files', to='scaffold_templates.File', validators=[cmdbox.scaffold_templates.validators.validate_folder]),
        ),
    ]