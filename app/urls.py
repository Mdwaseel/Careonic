from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.user_login, name='login'),  # Default to login
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('bp_tracking/', views.bp_tracking, name='bp_tracking'),
    path('report/', views.generate_report, name='report'),
    path('download_report/', views.download_report, name='download_report'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('get_entry_details/<str:date>/', views.get_entry_details, name='get_entry_details'),
    
]