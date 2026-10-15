from django.urls import path
from . import views

app_name = 'tracker'

urlpatterns = [
    path('', views.project_list, name='project_list_root'),
    path('projects/', views.project_list, name='project_list'),
    path('projects/<int:project_id>/', views.project_board, name='project_board'),
    path('projects/<int:project_id>/issues/create/', views.create_issue, name='create_issue'),
    path('issues/<int:issue_id>/', views.issue_detail, name='issue_detail'),
    path('issues/<int:issue_id>/update-status/', views.update_issue_status, name='update_issue_status'),
    path('issues/<int:issue_id>/status/', views.update_issue_status, name='update_issue_status_alias'),
    path('issues/<int:issue_id>/comments/add/', views.add_comment, name='add_comment'),
    path('health/', views.health_check, name='health_check'),
]
