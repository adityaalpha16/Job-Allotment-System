from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    
    path('jobs/', views.job_board, name='job_board'),
    path('jobs/create/', views.job_create, name='job_create'),
    path('jobs/<int:job_id>/edit/', views.job_edit, name='job_edit'),
    path('jobs/<int:job_id>/delete/', views.job_delete, name='job_delete'),
    path('jobs/<int:job_id>/status/', views.job_update_status, name='job_update_status'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    
    path('team/', views.team_management, name='team_management'),
    path('team/create/', views.team_create, name='team_create'),
    path('team/<int:user_id>/edit/', views.team_edit, name='team_edit'),
    path('team/<int:user_id>/delete/', views.team_delete, name='team_delete'),
    path('team/<int:user_id>/restore/', views.team_restore, name='team_restore'),
    path('team/import/', views.team_import, name='team_import'),
    path('previous-contributors/', views.previous_contributors, name='previous_contributors'),
    
    path('api/dashboard-stats/', views.dashboard_stats_api, name='dashboard_stats_api'),
]
