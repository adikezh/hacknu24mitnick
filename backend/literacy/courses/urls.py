from django.urls import path, include

from courses.views import *

app_name = "courses"

url_courses = [
    path("create_course", CreateCourse.as_view(), name="course_create"),
    path("list_course", CoursesList.as_view(), name="course_list"),
    path("detail_course/<slug:slug>", CourseDetail.as_view(), name="course_detail")
]

url_lessons = [
    path("create_lesson", CreateLesson.as_view(), name="lesson_create"),
    path("list_lesson", LessonList.as_view(), name="lesson_list"),
    path("detail_lesson/<slug:slug>", LessonDetail.as_view(), name="lesson_detail"),
]

urlpatterns = [
    path("", BasePage.as_view()),
    path("course/", include(url_courses)),
    path("lesson/", include(url_lessons)),
]
