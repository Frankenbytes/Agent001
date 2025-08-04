from django.contrib import admin
from django.urls import path
from soc_analyzer.views import (
    alert_view,
    stream_alert_view,
    chat_page,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('alerts/', alert_view, name='alert_view'),
    path('alerts/stream/', stream_alert_view, name='stream_alert_view'),
    path('chat/', chat_page, name='chat_page'),
]
