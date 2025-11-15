from django.urls import re_path
from .consumer import PresenceConsumer, PresenceConsumerSubmited

websocket_urlpatterns = [
    re_path(r"^ws/presence/$", PresenceConsumer.as_asgi()),
    re_path(r"^ws/presence/submited/$", PresenceConsumerSubmited.as_asgi()),
]
