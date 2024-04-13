from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404
from django.views.generic import CreateView
from django.views.generic.edit import View, ProcessFormView
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse_lazy, reverse

from courses.forms import CreateLessonForm, CreateCourseForm
from courses.models import Course, Lesson, Quiz


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context

    def get_quizes(self, lesson: Lesson):
        return lesson.quizes.all()


class LessonList(ListView):
    model = Lesson
    template_name = "courses/lessons/list.html"


class CreateLesson(CreateView):
    model = Lesson
    template_name = "courses/lessons/create.html"
    form_class = CreateLessonForm

    def get_success_url(self):
        return reverse("courses:lesson_detail", kwargs={"slug": self.object.slug})

