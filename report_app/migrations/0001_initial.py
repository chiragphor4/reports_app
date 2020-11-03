# Generated by Django 3.1.2 on 2020-11-02 08:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='status',
            fields=[
                ('pk_status_code', models.AutoField(primary_key=True, serialize=False)),
                ('status_name', models.CharField(max_length=100)),
                ('created_by', models.CharField(max_length=100)),
                ('created_date_time', models.DateTimeField(auto_now_add=True)),
                ('modified_by', models.CharField(blank=True, max_length=100, null=True)),
                ('modified_date_time', models.DateTimeField(auto_now_add=True, null=True)),
            ],
        ),
    ]