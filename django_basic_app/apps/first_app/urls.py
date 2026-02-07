from django.urls import path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()

app_name = "apps.first_app"

urlpatterns = [
    path("", views.FirstAppListView.as_view()),
    path("<int:pk>/", views.FirstAppDetailView.as_view()),
]
