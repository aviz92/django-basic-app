from django.urls import path
from rest_framework import routers

from . import views


router = routers.DefaultRouter()

app_name = 'apps.second_app'

urlpatterns = [
    path('', views.SecondAppListView.as_view()),
    path('<int:pk>/', views.SecondAppDetailView.as_view()),
]
