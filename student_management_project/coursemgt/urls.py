from django.urls import path

from . import views

urlpatterns = [
    path("", views.course_home, name="course_home"),
    path("course_add", views.course_add, name="course_add"),
    path("course_delete/<str:c_id>", views.course_delete),
    path("course_update/<str:c_id>", views.course_update),

    path("subject_add", views.subject_add, name="subject_add"),
    path("subject_home", views.subject_home, name="subject_home"),
    path("subject_delete/<str:sb_id>", views.subject_delete),
    path("subject_update/<str:sb_id>", views.subject_update),
    path("subject_do_update/<str:sb_id>",views.subject_do_update),
    path("add_subjectsincourse", views.add_subjectsincourse, name="add_subjectsincourse"),
]