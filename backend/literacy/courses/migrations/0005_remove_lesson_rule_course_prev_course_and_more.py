# Generated by Django 5.0.4 on 2024-04-14 04:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0004_lesson_description_lesson_summary'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lesson',
            name='rule',
        ),
        migrations.AddField(
            model_name='course',
            name='prev_course',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='next_course', to='courses.course'),
        ),
        migrations.AddField(
            model_name='lesson',
            name='prev_lesson',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='next_lesson', to='courses.lesson'),
        ),
    ]
