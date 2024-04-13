from django.db import models

# Create your models here.


class Courses(models.Model):
    name = models.CharField()
    slug = models.SlugField()


class Lessons(models.Model):
    name = models.CharField()
    file = models.FileField()


class Quiz(models.Model):
    question = models.CharField()
    type = models.CharField()
    lesson = models.ForeignKey("Lessons", related_name="quizes", on_delete=models.CASCADE)


class Answers(models.Model):
    answer = models.CharField()
    quiz = models.ForeignKey("Quiz", related_name="reviews", on_delete=models.CASCADE)
    is_right = models.BooleanField()
