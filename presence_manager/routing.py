from django.urls import re_path
from .consumer import SeancesConsumer

websocket_urlpatterns = [
    re_path(r"^ws/seances/dispatch/$", SeancesConsumer.as_asgi()),
]
