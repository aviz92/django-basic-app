from django.urls import path
from rest_framework import routers

from . import views


router = routers.DefaultRouter()

app_name = 'apps.first_app'

urlpatterns = [
    path('', views.FirstAppView.as_view()),
    path('<int:pk>/', views.FirstAppView.as_view()),
]
