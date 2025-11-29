from django.contrib import admin
from presence_manager.models import (
    Cours,
    HoraireCours,
    Presence,
    Classe,
    SeanceCours,
    Etudiant,
    Professeur,
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
        "classe",
        "volume_horaire",
        "status",
        "created_at",
    )
    search_fields = ("nom", "description", "status")
    list_filter = ("status",)
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
    list_display = (
        "cours_nom",
        "seance_infos",
        "etudiant_nom_complet",
        "etudiant_classe",
        "present",
    )

    list_filter = (
        "present",
        "seance_cours__horaire_cours__cours",
        "etudiant__classe",
    )

    search_fields = (
        "etudiant__utilisateur__nom",
        "etudiant__utilisateur__postnom",
        "etudiant__matricule",
        "seance_cours__horaire_cours__cours__nom",
    )

    ordering = ("seance_cours",)

    # Optimisation queries
    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related(
                "etudiant",
                "etudiant__utilisateur",
                "etudiant__classe",
                "seance_cours",
                "seance_cours__horaire_cours",
                "seance_cours__horaire_cours__cours",
            )
        )

    # ----- Colonnes personnalisées -----

    def cours_nom(self, obj):
        return obj.seance_cours.horaire_cours.cours.nom

    cours_nom.short_description = "Cours"

    def seance_infos(self, obj):
        se = obj.seance_cours
        return f"Seance {se.id} ({se.heure_debut} - {se.heure_fin})"

    seance_infos.short_description = "Séance"

    def etudiant_nom_complet(self, obj):
        u = obj.etudiant.utilisateur
        return f"{u.nom} {u.postnom}"

    etudiant_nom_complet.short_description = "Étudiant"

    def etudiant_classe(self, obj):
        return obj.etudiant.classe.nom if obj.etudiant.classe else "Aucune"

    etudiant_classe.short_description = "Classe"


@admin.register(Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = (
        "matricule",
        "nom_complet",
        "email",
        "classe_display",
    )

    list_filter = ("classe",)

    search_fields = (
        "matricule",
        "utilisateur__nom",
        "utilisateur__postnom",
        "utilisateur__email",
    )

    ordering = ("matricule",)

    # Optimisation des requêtes
    def get_queryset(self, request):
        return super().get_queryset(request).select_related("utilisateur", "classe")

    # Méthodes personnalisées d'affichage
    def nom_complet(self, obj):
        return f"{obj.utilisateur.nom}{obj.utilisateur.postnom}"

    nom_complet.short_description = "Nom complet"

    def email(self, obj):
        return obj.utilisateur.email

    email.short_description = "Email"

    def classe_display(self, obj):
        if obj.classe:
            return (
                f"{obj.classe.nom} ({obj.classe.section.nom})"
                if hasattr(obj.classe, "section")
                else obj.classe.nom
            )
        return "Aucune"

    classe_display.short_description = "Classe"


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ("utilisateur",)


# ============================
#   Custom titles
# ============================
admin.site.site_header = "Gestion des Présences"
admin.site.site_title = "Gestion des Présences - Administration"
admin.site.index_title = (
    "Bienvenue sur le portail d'administration de la gestion des présences"
)
