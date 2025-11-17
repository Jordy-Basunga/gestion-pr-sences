from django.urls import re_path
from .consumer import SenderCours, PresenceConsumerSubmited, GenerateSeance

websocket_urlpatterns = [
    re_path(r"^ws/presence/$", SenderCours.as_asgi()),
    re_path(r"^ws/presence/submited/$", PresenceConsumerSubmited.as_asgi()),
    re_path(r"^ws/get/seances/$", GenerateSeance.as_asgi()),
]
