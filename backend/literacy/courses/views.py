import json

import requests
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from courses.forms import CreateLessonForm, CreateCourseForm
from courses.models import Course, Lesson, Result


# Create your views here.


class BasePage(TemplateView):
    template_name = "courses/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class CoursesList(ListView):
    model = Course
    template_name = "courses/course/course-list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        print(context)

        return context


class CourseDetail(DetailView):
    model = Course
    template_name = "courses/course_detail.html"

    def get_queryset(self):
        slug = get_object_or_404(Course, slug=self.kwargs.get("course"))


class CreateCourse(CreateView, ):
    model = Course
    template_name = "courses/course/create.html"
    form_class = CreateCourseForm
    success_url = reverse_lazy('courses:course_list')


class LessonDetail(DetailView):
    model = Lesson
    template_name = "courses/lessons/detail.html"


class LessonList(ListView):
    model = Lesson
    template_name = "courses/lessons/list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(object_list=object_list, **kwargs)
        t = []
        for lesson in context["lesson_list"]:
            a = []
            for quiz in lesson.quizes.all():
                percents = quiz.results.filter(user=self.request.user).first()
                if percents:
                    a.append(percents.percent)
            lesson.percent = sum(a) / len(a) if a else 0
            t.append(lesson)
        context["lesson_list"] = t
        print(context)
        return context


class CreateLesson(CreateView):
    model = Lesson
    template_name = "courses/lessons/create.html"
    form_class = CreateLessonForm

    def get_success_url(self):
        return reverse("courses:lesson_detail", kwargs={"slug": self.object.slug})


class LessonTest(DetailView):
    model = Lesson
    template_name = "courses/lessons/test.html"

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        quiz = lesson.quizes.filter(id=request.POST["quiz"]).first()
        if Result.objects.get(user=request.user, quiz=quiz):
            return JsonResponse({"error": "You have already passed this quiz"})

        submitted_answers = {i: request.POST[i] for i in request.POST.keys() if
                             i not in ["quiz", "csrfmiddlewaretoken"]}
        correct_answers = {str(answer.id): answer.is_right for answer in quiz.questions.all()}
        results = {question_id: not not submitted_answers.get(question_id) if correct_answers.get(
            question_id) is True else not submitted_answers.get(question_id) for question_id in correct_answers.keys()}

        percent = sum(results.values()) / len(results) * 100

        result = Result.objects.create(
            user=request.user,
            quiz=quiz,
            percent=percent
        )

        return JsonResponse(results)


@csrf_exempt
def translate(request):
    if request.method != "POST":
        return JsonResponse({"error": "Method not allowed", 'info': "Available languages: en, ru, kk"})
    data = json.loads(request.body.decode('utf-8'))
    texts = data.get("texts")
    source_language = data.get("sourceLanguageCode")
    target_language = data.get("targetLanguageCode")

    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    payload = {
        "texts": texts,
        "sourceLanguageCode": source_language,
        "targetLanguageCode": target_language,
        "format": "PLAIN_TEXT",
        "folderId": "b1g7eqq5q277knhj42b2",
        "speller": True
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Api-Key AQVN0bZNKdTiZI1L7whsPeoSRdfODJpQA05vdb-Q"
    }

    response = requests.post(url, json=payload, headers=headers)
    return JsonResponse(response.json())
