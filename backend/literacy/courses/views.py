from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse

from courses.forms import CreateLessonForm, CreateCourseForm
from courses.models import Course, Lesson, Quiz, Result


# Create your views here.

class BasePage(TemplateView):
    template_name = "courses/index.html"


class CoursesList(ListView):
    model = Course
    template_name = "courses/course_list.html"

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

    def post(self, request, *args, **kwargs):
        lesson = self.get_object()
        quiz = lesson.quizes.filter(id=request.POST["quiz"]).first()
        if Result.objects.get(user=request.user, quiz=quiz):
            return JsonResponse({"error": "You have already passed this quiz"})

        submitted_answers = {i: request.POST[i] for i in request.POST.keys() if i not in ["quiz", "csrfmiddlewaretoken"]}
        correct_answers = {str(answer.id): answer.is_right for answer in quiz.questions.all()}
        results = {question_id: not not submitted_answers.get(question_id) if correct_answers.get(question_id) == True else not submitted_answers.get(question_id) for question_id in correct_answers.keys()}

        percent = sum(results.values()) / len(results) * 100

        result = Result.objects.create(
            user=request.user,
            quiz=quiz,
            percent=percent
        )

        return JsonResponse(results)


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

