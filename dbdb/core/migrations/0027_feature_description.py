# Generated by Django 3.1.14 on 2022-07-04 19:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0026_auto_20220626_1511'),
    ]

    operations = [
        migrations.AddField(
            model_name='feature',
            name='description',
            field=models.TextField(blank=True, help_text='This field supports Markdown Syntax'),
        ),
    ]