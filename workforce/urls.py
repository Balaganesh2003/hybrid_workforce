from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),

    # Registration & Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards
    path('dashboard/client/', views.dashboard_client, name='dashboard_client'),
    path('dashboard/freelancer/', views.dashboard_freelancer, name='dashboard_freelancer'),
    path('dashboard/fulltime/', views.dashboard_full_time, name='dashboard_full_time'),

    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/manage/', views.manage_profile_view, name='manage_profile'),
    path('profile/<int:user_id>/', views.view_profile, name='view_profile'),

    # Projects
    path('projects/create/', views.create_project_view, name='create_project'),
    path('projects/', views.client_projects_view, name='projects'),
    path('projects/<int:project_id>/team/', views.select_team_view, name='select_team'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.edit_project, name='edit_project'),
    path("project/<int:pk>/", views.project_detail, name="project_detail"),
    path("projects/<int:project_id>/messages/", views.message_team_view, name="message_team"),
    path("project/<int:pk>/update-progress/", views.update_progress, name="update_progress"),
    path('project/<int:pk>/mark-complete/', views.mark_complete, name='mark_complete'),
    

    # Budget Prediction
    path('budget/predict/', views.predict_budget_view, name='predict_budget'),


    # Notifications
    path('notifications/', views.notifications_view, name='notifications'),

    # Talent Search
    path('talent/search/', views.talent_search_view, name='talent_search'),

    # Reporting (Admin)
    path('reporting/', views.reporting_view, name='reporting'),

    # Settings
    path('settings/', views.settings_view, name='settings'),
]
