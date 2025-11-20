from django.contrib import admin
from presence_manager.models import (
    Cours,
    HoraireCours,
    Presence,
    Classe,
    SeanceCours,
)


@admin.register(Classe)
class ClasseAdmin(admin.ModelAdmin):
    """
    Représente une classe d'étudiants dans l'institution,
    """

    list_display = (
        "nom",
        "description",
        "annee_academique",
        "created_at",
        "code_terminal",
    )
    search_fields = ("nom", "description", "annee_academique")
    ordering = ("-created_at",)


# ============================
#   Admin Cours
# ============================
@admin.register(Cours)
class CoursAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "description",
        "volume_horaire",
        "status",
        "id_professeur",
        "created_at",
    )
    search_fields = ("nom", "description", "status")
    list_filter = ("status", "id_professeur")
    ordering = ("-created_at",)


# ============================
#   Admin HoraireCours
# ============================
@admin.register(HoraireCours)
class HoraireCoursAdmin(admin.ModelAdmin):
    list_display = ("cours", "jour_semaine", "heure_debut", "heure_fin")
    search_fields = ("cours__nom", "jour_semaine")
    list_filter = ("jour_semaine",)
    ordering = ("cours", "jour_semaine")


# ============================
#   Admin SeanceCours
# ============================
@admin.register(SeanceCours)
class SeanceCoursAdmin(admin.ModelAdmin):
    list_display = (
        "horaire_cours",
        "date_seance",
        "heure_debut",
        "heure_fin",
        "status",
    )
    search_fields = ("horaire_cours__cours__nom", "date_seance")
    list_filter = ("date_seance",)
    ordering = ("-date_seance",)


# ============================
#   Admin Presence
# ============================
@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("seance_cours", "id_etudiant", "present")
    search_fields = ("id_etudiant", "seance_cours__horaire_cours__cours__nom")
    list_filter = ("present",)
    ordering = ("seance_cours", "id_etudiant")


# ============================
#   Custom titles
# ============================
admin.site.site_header = "Gestion des Présences"
admin.site.site_title = "Gestion des Présences - Administration"
admin.site.index_title = (
    "Bienvenue sur le portail d'administration de la gestion des présences"
)
