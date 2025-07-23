from django.contrib import admin
from django.urls import path
from soc_analyzer.views import alert_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('alerts/', alert_view, name='alert_view'),
]