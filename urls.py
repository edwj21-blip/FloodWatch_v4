from django.urls import path
from . import views

urlpatterns = [
    # Portal / landing
    path('portal/', views.portal_view, name='portal'),

    # Dashboard
    path('', views.home, name='home'),

    # Flood info
    path('alerts/', views.alerts_view, name='alerts'),
    path('water-levels/', views.water_levels_view, name='water_levels'),
    path('rescue-teams/', views.rescue_teams_view, name='rescue_teams'),
    path('control-rooms/', views.control_rooms_view, name='control_rooms'),

    # Reports
    path('report/', views.report_flood, name='report_flood'),
    path('report/success/<int:pk>/', views.report_success, name='report_success'),
    path('my-reports/', views.my_reports, name='my_reports'),
    path('admin-reports/', views.admin_reports_view, name='admin_reports'),
    path('admin-reports/action/<int:pk>/', views.admin_report_action, name='admin_report_action'),

    # API endpoints
    path('api/water-levels/', views.api_water_levels, name='api_water_levels'),
    path('api/weather-status/', views.api_weather_status, name='api_weather_status'),

    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]
