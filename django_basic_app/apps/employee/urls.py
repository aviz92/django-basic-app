from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

app_name = "apps.employee"

urlpatterns = [
    path("", views.EmployeeListView.as_view()),
    path("<int:pk>/", views.EmployeeDetailView.as_view()),
]
