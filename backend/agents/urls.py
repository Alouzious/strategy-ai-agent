from django.urls import path
from .views import RunAgentView, HealthCheckView

urlpatterns = [
    path('run-agent/', RunAgentView.as_view(), name='run-agent'),
    path('health/', HealthCheckView.as_view(), name='health'),
]