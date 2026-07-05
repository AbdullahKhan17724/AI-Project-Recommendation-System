from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('learning-path/', views.learning_path, name='learning_path'),
    path('add-skill/', views.add_skill_from_learning, name='add_skill'),
    path('project/<int:project_id>/', views.project_detail, name='project_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('beginner-select/', views.beginner_select_interests, name='beginner_select'),
    path('api/recommendations/', views.api_recommendations_json, name='api_recommendations'),
path('profile/', views.profile, name='profile'),
]
