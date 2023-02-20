from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('champion_mastery/', views.champion_mastery, name='champion_mastery'),
    #path('match_history/', views.get_match_history, name='match_history'),
]