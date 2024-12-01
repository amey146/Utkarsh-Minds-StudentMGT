from django.urls import path

from studentmgt import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("", views.student_home, name="student_home"),
    path("student_add", views.student_add, name="student_add"),
    path("student_delete/<int:st_id>",views.student_delete),
    path("student_update/<int:st_id>",views.student_update),
    path("student_do_update/<int:st_id>",views.student_do_update),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)