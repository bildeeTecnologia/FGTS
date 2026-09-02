from django.urls import path
from .views import DashboardPerformanceView

urlpatterns = [
    path('dashboard/', DashboardPerformanceView.as_view(), name='performance-dashboard'),
]
