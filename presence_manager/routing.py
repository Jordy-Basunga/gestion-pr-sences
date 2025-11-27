from django.urls import re_path
from .consumer import SeancesConsumer, SubmitePresence

websocket_urlpatterns = [
    re_path(r"^ws/seances/dispatch/$", SeancesConsumer.as_asgi()),
    re_path(r"^ws/seances/submit/presence/$", SubmitePresence.as_asgi()),
    # re_path(r"^ws/terminal/dispatch/$", SeanceDispatchConsumer.as_asgi()),
]
