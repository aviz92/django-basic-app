from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

app_name = "apps.department"

urlpatterns = [
    path("", views.DepartmentListView.as_view()),
    path("<int:pk>/", views.DepartmentDetailView.as_view()),
]
