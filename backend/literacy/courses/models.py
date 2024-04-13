from django.db import models

# Create your models here.


class Courses(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()


class Lesson(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()


class Quiz(models.Model):
    question = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lesson = models.ForeignKey("Lesson", related_name="quizes", on_delete=models.CASCADE)


class Answer(models.Model):
    answer = models.CharField(max_length=255)
    quiz = models.ForeignKey("Quiz", related_name="reviews", on_delete=models.CASCADE)
    is_right = models.BooleanField()


class Video(models.Model):
    url = models.CharField(max_length=255)
    lesson = models.ForeignKey("Lesson", related_name="videos", on_delete=models.CASCADE)
