from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'employees', views.EmployeeViewSet, basename='employee')
router.register(r'devices', views.DeviceViewSet, basename='device')
router.register(r'punch-logs', views.PunchLogViewSet, basename='punch-log')

urlpatterns = [
    path('', include(router.urls)),
]