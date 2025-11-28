from django.urls import path
from .views import submit_presence

urlpatterns = [
    path("submit/", submit_presence, name="submit-presence"),
]
