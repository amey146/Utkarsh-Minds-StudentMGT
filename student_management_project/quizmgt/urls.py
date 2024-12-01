from django.urls import path

from quizmgt import views

urlpatterns = [
    path("", views.quiz_home, name="quiz_home"),
    path("quiz_add", views.quiz_add, name="quiz_add"),
    path("quiz_list", views.quiz_list, name="quiz_list"),
    path("report_list", views.report_list, name="report_list"),
    path('generate-reports/', views.report_generation, name='report_generation'),
    path("subject_select/<str:c_id>", views.subject_select),
    path("student_list/<str:c_id>/<str:sbname>/", views.student_list),
    path("quiz_submit/<str:sbname>", views.quiz_submit, name="quiz_submit"),
    path('download_csv/<str:file_name>/<str:dir_name>/', views.download_csv, name='download_csv'),
    path('quiz/delete/<str:file_name>/<str:dir_name>/', views.delete_csv, name='delete_csv'),
]
