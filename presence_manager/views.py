import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.utils.timezone import now
from django.db import DatabaseError

from .serializer import PresenceSubmitSerializer
from .models import Etudiant, Classe, Cours, Presence, SeanceCours
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

logger = logging.getLogger(__name__)  # Logger du module


# ------------------------------
# Configuration du logger vers un fichier
logger = logging.getLogger("presence_manager")
logger.setLevel(logging.INFO)
# Créer un handler fichier
file_handler = logging.FileHandler("logs_presences.log")
file_handler.setLevel(logging.INFO)
# Format des logs
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
# Ajouter le handler au logger
if not logger.handlers:
    logger.addHandler(file_handler)
# -----


def get_object_or_error(model, **filters):
    """
    Récupère un objet ou retourne une réponse d'erreur standardisée.
    """
    try:
        return model.objects.get(**filters), None
    except model.DoesNotExist:
        return None, Response(
            {"error": f"{model.__name__} introuvable avec : {filters}"},
            status=status.HTTP_404_NOT_FOUND,
        )
    except DatabaseError as e:
        logger.error(f"Erreur DB lors de la récupération de {model.__name__}: {e}")
        return None, Response(
            {"error": "Erreur interne lors de la récupération des données."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
def submit_presence(request):
    # 1️⃣ Validation serializer
    serializer = PresenceSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        logger.warning(f"Payload invalide: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    matricule = data["matricule"]
    email = data["email"]
    classe_id = data["classe"]
    cours_id = data["cours"]

    # 2️⃣ Vérifier étudiant
    etudiant, error = get_object_or_error(Etudiant, matricule=matricule)
    if error:
        return error

    # 3️⃣ Vérifier classe
    classe, error = get_object_or_error(Classe, id=classe_id)
    if error:
        return error

    # 4️⃣ Vérifier appartenance
    if not classe.etudiants.filter(id=etudiant.id).exists():
        logger.warning(f"Étudiant {matricule} n'appartient pas à la classe {classe.id}")
        return Response(
            {"error": "Cet étudiant n'appartient pas à cette classe."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 5️⃣ Vérifier cours dans cette classe
    cours, error = get_object_or_error(Cours, id=cours_id, classe=classe)
    if error:
        return error

    # 6️⃣ Vérifier séance en cours
    today = now().date()
    try:
        seance = SeanceCours.objects.filter(
            horaire_cours__cours=cours, date_seance=today, status="en_cours"
        ).first()
    except DatabaseError as e:
        logger.error(f"Erreur DB lors de la vérification des séances : {e}")
        return Response(
            {"error": "Erreur interne lors de la vérification des séances."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not seance:
        logger.info(
            f"Aucune séance en cours pour cours {cours.id} - classe {classe.id}"
        )
        return Response(
            {"error": "Aucune séance en cours pour ce cours."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 7️⃣ Vérifier doublon présence
    if Presence.objects.filter(
        seance_cours=seance, etudiant=etudiant, present=True
    ).exists():
        logger.info(
            f"Présence déjà enregistrée pour étudiant {matricule} à la séance {seance.id}"
        )
        return Response(
            {"error": "Vous êtes déjà dans la liste."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # 8️⃣ Enregistrer présence
    try:
        presence = Presence.objects.create(
            seance_cours=seance,
            etudiant=etudiant,
            present=True,
        )
    except DatabaseError as e:
        logger.error(f"Erreur DB lors de l'enregistrement de la présence : {e}")
        return Response(
            {"error": "Erreur interne lors de l'enregistrement de la présence."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    logger.info(
        f"Présence enregistrée: etudiant={etudiant.matricule}, "
        f"classe={classe.id}, cours={cours.id}, seance={seance.id}"
    )

    # --- Envoi WebSocket ---
    try:
        channel_layer = get_channel_layer()
        group_name = f"presence_seance_{seance.id}"
        logger.debug(f"Envoi WebSocket au groupe {group_name}")

        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "presence_update",
                "data": {
                    "matricule": etudiant.matricule,
                    "nom": etudiant.utilisateur.nom,
                    "postnom": etudiant.utilisateur.postnom,
                    "classe": classe.id,
                    "cours": cours.nom,
                    "seance_id": seance.id,
                    "heure": now().strftime("%H:%M:%S"),
                    "status": "present",
                },
            },
        )

    except Exception as e:
        logger.error(f"Erreur WebSocket envoi: {e}")

    # 9️⃣ Réponse finale
    return Response(
        {
            "message": "Présence enregistrée avec succès.",
            "presence": {
                "etudiant": etudiant.utilisateur.nom,
                "matricule": etudiant.matricule,
                "classe": classe.id,
                "cours": cours.nom,
                "seance_id": seance.id,
            },
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
def get_seances_en_cours(request, cours_id):
    today = now().date()
    seances = SeanceCours.objects.filter(
        horaire_cours__cours_id=cours_id, date_seance=today, status="en_cours"
    )

    data = [
        {
            "id": s.id,
            "date": s.date_seance,
            "heure_debut": s.horaire_cours.heure_debut,
            "heure_fin": s.horaire_cours.heure_fin,
        }
        for s in seances
    ]

    return Response({"seances_en_cours": data}, status=200)


@api_view(["GET"])
def get_presences_seance(request, seance_id):
    presences = Presence.objects.filter(seance_cours_id=seance_id)

    data = [
        {
            "id": p.id,
            "matricule": p.etudiant.matricule,
            "nom": p.etudiant.utilisateur.nom,
            "postnom": p.etudiant.utilisateur.postnom,
            "present": p.present,
        }
        for p in presences
    ]

    return Response({"presences": data}, status=200)
