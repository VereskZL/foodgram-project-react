# Generated by Django 2.2.16 on 2023-04-03 17:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('food', '0002_alter_recipe_text'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='text',
            field=models.TextField(verbose_name='Текст'),
        ),
    ]
