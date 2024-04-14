from slugify import slugify
from django import forms

from courses.models import Lesson, Course


class CreateLessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['name', 'video', 'course']

    def save(self, commit=True):
        self.instance.slug = slugify(self.instance.name)
        return super().save(commit=commit)


class CreateCourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name',]

    def save(self, commit=True):
        self.instance.slug = slugify(self.instance.name)
        return super().save(commit=commit)

