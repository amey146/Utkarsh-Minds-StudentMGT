from django.urls import path

from . import views

urlpatterns = [
    path("", views.attendance_home, name="attendance_home"),
    path("attendance_add", views.attendance_add, name="attendance_add"),
    path("attendance_add_action", views.attendance_add_action, name="attendance_add_action"),
    path("attendance_list", views.attendance_list, name="attendance_list"),
    path("ind_attendance_list", views.ind_attendance_list, name="ind_attendance_list"),
    path('download_csv/<str:file_name>/<str:dir_name>/', views.download_csv, name='attendance_download_csv'),
    path('attendance/delete/<str:file_name>/<str:dir_name>/', views.delete_csv, name='attendance_delete_csv'),
]
