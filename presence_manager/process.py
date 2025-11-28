from datetime import date, datetime

from .utils import convertir_weekday_en_nom
from .models import HoraireCours, SeanceCours
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def generer_seances_du_jour():
    logger.info("Génération des séances du jour démarrée.")
    """
    Génère automatiquement les séances de cours pour aujourd'hui selon les horaires définis.
    - Ne fonctionne que du lundi au vendredi
    - Vérifie l'heure actuelle pour créer les séances seulement si l'heure de début est atteinte
    - Évite les doublons
    """
    today = date.today()
    now = datetime.now().time()
    weekday = today.weekday()  # 0 = Lundi, ..., 6 = Dimanche
    print(f"[Tâche] Génération des séances pour le jour {today} (weekday={weekday})")
    # Étape 1 : Vérifier si c'est un week-end
    if weekday in [5, 6]:
        return  # Samedi ou dimanche → rien à générer

    # Étape 2 : Récupérer les horaires du jour
    jour_actuel = convertir_weekday_en_nom(weekday)
    horaires_du_jour = HoraireCours.objects.filter(jour_semaine=jour_actuel).order_by(
        "heure_debut"
    )
    print(f"[Tâche] Horaires trouvés pour {jour_actuel} : {horaires_du_jour}")
    # Étape 3 : Vérifier et créer les séances
    for horaire in horaires_du_jour:
        # Vérifier si la séance existe déjà pour aujourd'hui
        existe = SeanceCours.objects.filter(
            horaire_cours=horaire, date_seance=today
        ).exists()

        if existe:
            continue  # passe au cours suivant

        # Vérifier si l'heure de début est atteinte
        if horaire.heure_debut <= now:
            # Créer la séance
            SeanceCours.objects.create(
                horaire_cours=horaire,
                date_seance=today,
                heure_debut=horaire.heure_debut,
                heure_fin=horaire.heure_fin,
            )


def validate_presence_payload(content):
    """
    Valide le payload envoyé dans le WebSocket.
    Fonctionne comme un serializer DRF mais sans DRF.
    """

    errors = {}
    validated = {}

    # ------- matricule -------
    matricule = content.get("matricule")
    if not matricule:
        errors["matricule"] = "Le matricule est requis."
    else:
        validated["matricule"] = matricule

    # ------- email -------
    email = content.get("email")
    if not email:
        errors["email"] = "L'email est requis."
    else:
        # Validation simple de l'email
        if "@" not in email or "." not in email:
            errors["email"] = "Email invalide."
        else:
            validated["email"] = email

    # ------- classe -------
    classe = content.get("classe")
    if not classe:
        errors["classe"] = "La classe est requise."
    else:
        validated["classe"] = classe

    # ------- cours -------
    cours = content.get("cours")
    if not cours:
        errors["cours"] = "Le cours est requis."
    else:
        validated["cours"] = cours

    # S'il y a des erreurs -> on les retourne
    if errors:
        return {"valid": False, "errors": errors}

    # Sinon -> données validées
    return {"valid": True, "data": validated}

    # from datetime import date
    # from asgiref.sync import sync_to_async
    # from django.core.exceptions import ObjectDoesNotExist

    # async def process_presence_submission(payload):
    #     """
    #     Fonction de traitement complet d’une présence.
    #     Prend le payload reçu du WebSocket et enregistre la présence.

    #     payload attendu :
    #     {
    #         "matricule": "ET101",
    #         "email": "student@example.com",
    #         "classe": "L2 IG",
    #         "cours": "Algorithmique"
    #     }
    #     """
    #     from .models import HoraireCours, SeanceCours

    #     errors = {}

    #     matricule = payload.get("matricule")
    #     email = payload.get("email")
    #     classe_nom = payload.get("classe")
    #     cours_nom = payload.get("cours")

    #     # ============================
    #     # VALIDATION DES CHAMPS
    #     # ============================

    #     if not matricule:
    #         errors["matricule"] = "Le matricule est requis."

    #     if not email:
    #         errors["email"] = "L'email est requis."

    #     if not classe_nom:
    #         errors["classe"] = "La classe est requise."

    #     if not cours_nom:
    #         errors["cours"] = "Le cours est requis."

    #     if errors:
    #         return {"valid": False, "errors": errors}

    # ============================
    # 1. Vérification étudiant
    # ============================
    from presence_manager.models import (
        Etudiant,
        Classe,
        Cours,
        HoraireCours,
        SeanceCours,
        Presence,
    )

    try:
        etudiant = await sync_to_async(Etudiant.objects.select_related("classe").get)(
            matricule=matricule
        )
    except ObjectDoesNotExist:
        return {"valid": False, "errors": {"matricule": "Étudiant introuvable."}}

    # Vérifier cohérence email
    if etudiant.utilisateur.email != email:
        return {
            "valid": False,
            "errors": {"email": "Email ne correspond pas à cet étudiant."},
        }


#     # ============================
#     # 2. Vérification classe
#     # ============================
#     if not etudiant.classe or etudiant.classe.nom != classe_nom:
#         return {
#             "valid": False,
#             "errors": {"classe": "L'étudiant n'appartient pas à cette classe."},
#         }

#     classe = etudiant.classe

#     # ============================
#     # 3. Vérification cours
#     # ============================
#     try:
#         cours = await sync_to_async(Cours.objects.get)(nom=cours_nom, classe=classe)
#     except ObjectDoesNotExist:
#         return {
#             "valid": False,
#             "errors": {"cours": "Ce cours n'appartient pas à cette classe."},
#         }

#     # ============================
#     # 4. Trouver la séance du jour
#     # ============================
#     today = date.today()

#     try:
#         # séance générée par ton cron
#         seance = await sync_to_async(
#             SeanceCours.objects.select_related(
#                 "horaire_cours", "horaire_cours__cours"
#             ).get
#         )(horaire_cours__cours=cours, date_seance=today)

#     except ObjectDoesNotExist:
#         return {
#             "valid": False,
#             "errors": {"seance": "Aucune séance prévue aujourd'hui pour ce cours."},
#         }

#     # ============================
#     # 5. Vérifier si présence existe déjà
#     # ============================
#     presence, created = await sync_to_async(Presence.objects.get_or_create)(
#         seance_cours=seance,
#         etudiant=etudiant,
#         defaults={"present": True},
#     )

#     if not created:
#         # l'étudiant est déjà marqué
#         return {
#             "valid": True,
#             "message": "Présence déjà enregistrée auparavant.",
#             "presence_id": presence.id,
#             "already": True,
#         }

#     # ============================
#     # 6. Présence enregistrée
#     # ============================
#     return {
#         "valid": True,
#         "message": "Présence enregistrée avec succès.",
#         "presence_id": presence.id,
#         "cours": cours.nom,
#         "classe": classe.nom,
#         "date": str(today),
#         "etudiant": {
#             "matricule": etudiant.matricule,
#             "nom": etudiant.utilisateur.nom,
#             "postnom": etudiant.utilisateur.postnom,
#             "email": etudiant.utilisateur.email,
#         },
#     }
