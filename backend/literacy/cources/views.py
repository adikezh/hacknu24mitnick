from django.views.generic.list import ListView
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView
from django.shortcuts import get_object_or_404

from cources.models import Courses


# Create your views here.

class BasePage(TemplateView):
    template_name = "courses/index.html"


class CoursesList(ListView):
    model = Courses
    template_name = "cources/course_list.html"


class CourseDetail(DetailView):
    model = Courses
    template_name = "cources/course_detail.html"

    def get_queryset(self):
        slug = get_object_or_404(Courses, slug=self.kwargs.get("course"))


