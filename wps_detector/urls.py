from django.urls import path
from . import views

app_name = 'wps_detector'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/chart/status-pie/', views.chart_status_pie, name='chart_status_pie'),
    path('api/chart/failed-attempts/', views.chart_failed_attempts, name='chart_failed_attempts'),
    path('api/chart/timeline/', views.chart_timeline, name='chart_timeline'),
    path('api/chart/event-types/', views.chart_event_types, name='chart_event_types'),
    path('api/scan/', views.run_scan, name='run_scan'),
    path('report.png', views.report_image, name='report_image'),
]
