from django.urls import path

from . import views

urlpatterns = [
    path('', views.champion_mastery, name='champion_mastery'),
]