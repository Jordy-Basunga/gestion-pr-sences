from django.urls import path
from .views import (
    download_qr,
    generate_qr,
    submit_presence,
    get_presences_seance,
    get_seances_en_cours,
  
)

urlpatterns = [
    # soumission de présence
    path("submit/", submit_presence, name="submit-presence"),
    # présences et séances
    path("seances/<int:cours_id>/", get_seances_en_cours, name="get-seances-en-cours"),
    path("<int:seance_id>/", get_presences_seance, name="get-presences-seance"),
    # create user
    # QR Code URLs
    path("qr/generate/", generate_qr, name="generate_qr"),
    path("qr/<str:matricule>/download/", download_qr, name="download_qr"),


]
