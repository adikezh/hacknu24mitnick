from django.db import models
from django.urls import reverse


# Create your models here.


class Course(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    # prev_course = models.ForeignKey(
    #     "Course",
    #     related_name="next_course",
    #     on_delete=models.CASCADE,
    #     null=True,
    #     blank=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("courses:course_detail", kwargs={"slug": self.slug})


class Lesson(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    video = models.CharField(max_length=500)
    rule = models.TextField()
    course = models.ForeignKey("Course", related_name="lessons", on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Quiz(models.Model):
    question = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    lesson = models.ForeignKey("Lesson", related_name="quizes", on_delete=models.CASCADE)

    def __str__(self):
        return self.question


class Answer(models.Model):
    answer = models.CharField(max_length=255)
    quiz = models.ForeignKey("Quiz", related_name="questions", on_delete=models.CASCADE)
    is_right = models.BooleanField()

    def __str__(self):
        return self.answer


class Result(models.Model):
    user = models.ForeignKey("authorization.User", related_name="results", on_delete=models.CASCADE)
    quiz = models.ForeignKey("Quiz", related_name="results", on_delete=models.CASCADE)
    percent = models.FloatField()
