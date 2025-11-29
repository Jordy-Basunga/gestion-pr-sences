from django.urls import path
from .views import submit_presence, get_presences_seance, get_seances_en_cours

urlpatterns = [
    path("submit/", submit_presence, name="submit-presence"),
    path("seances/<int:cours_id>/", get_seances_en_cours, name="get-seances-en-cours"),
    path("<int:seance_id>/", get_presences_seance, name="get-presences-seance"),
]
