# Generated by Django 4.1.2 on 2022-10-12 05:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0003_alter_type_parent'),
    ]

    operations = [
        migrations.AddField(
            model_name='type',
            name='name',
            field=models.CharField(default=0, max_length=100),
            preserve_default=False,
        ),
    ]
