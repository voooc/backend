# Generated by Django 2.2.18 on 2023-05-25 13:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('news', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='banner',
            options={'ordering': ['-order']},
        ),
        migrations.AddField(
            model_name='banner',
            name='link',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='banner',
            name='order',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='news',
            name='url',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
