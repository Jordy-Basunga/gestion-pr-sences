from django.urls import path
from .views import (
    UtilisateurCreateView,
   
)

#----------------------- creation d'utilisateur -----------------------

urlpatterns = [path("create/", UtilisateurCreateView.as_view(), name="user-create"),]