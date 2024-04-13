from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView
from django.views.generic.edit import View, ProcessFormView

from courses.models import Courses, Lesson, Quiz


# Create your views here.

class BasePage(TemplateView):
    template_name = "courses/index.html"


class CoursesList(ListView):
    model = Courses
    template_name = "courses/course_list.html"


class CourseDetail(DetailView):
    model = Courses
    template_name = "courses/course_detail.html"

    def get_queryset(self):
        slug = get_object_or_404(Courses, slug=self.kwargs.get("course"))


class CreateCourse(CreateView):
    model = Courses
    template_name = "courses/course_create.html"


class LessonDetail(DetailView):
    model = Lesson
    template_name = "courses/lessons/detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_quizes(self, lesson: Lesson):
        return lesson.quizes.all()


class CreateLesson(CreateView):
    model = Lesson
    template_name = "courses/lessons/create.html"


def get_all_questions_from_quiz(request):
    quiz = Quiz.objects.get(lesson=request.POST)
