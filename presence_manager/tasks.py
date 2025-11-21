from celery import shared_task
from django.core.cache import cache

from celery import shared_task
from django.utils import timezone
from presence_manager.models import SeanceCours
import logging

from datetime import date, datetime
from presence_manager.models import *
from .utils import convertir_weekday_en_nom, groupe_name
from .models import HoraireCours, SeanceCours
from celery import shared_task
import logging

# presence_manager/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from presence_manager.models import SeanceCours

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)


@shared_task
def run_tasks():
    # print("Running scheduled tasks...")
    # logger.info("Running scheduled tasks...")
    pass


# ------------------------------------------------------------------------------------
from celery import shared_task
from django.core.cache import cache
from datetime import date, datetime
from presence_manager.models import HoraireCours, SeanceCours
from .utils import convertir_weekday_en_nom

import logging

logger = logging.getLogger(__name__)

# ------------------------------
# Configuration du logger vers un fichier
logger = logging.getLogger("presence_manager")
logger.setLevel(logging.INFO)
# Créer un handler fichier
file_handler = logging.FileHandler("logs_seances.log")
file_handler.setLevel(logging.INFO)
# Format des logs
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
# Ajouter le handler au logger
if not logger.handlers:
    logger.addHandler(file_handler)
# -----


@shared_task
def generer_seances_du_jour():
    """
    Génère automatiquement les séances de cours pour aujourd'hui selon les horaires définis.
    - Ne fonctionne que du lundi au vendredi.
    - Vérifie l'heure actuelle pour créer les séances seulement si l'heure de début est atteinte.
    - Évite les doublons.
    - Utilise Redis pour mettre en cache les horaires du jour.
    """
    today = date.today()
    now = datetime.now().time()
    weekday = today.weekday()  # 0=Lundi, 6=Dimanche

    logger.info(f"Génération des séances pour le jour {today} (weekday={weekday})")

    # Ne rien faire le week-end
    if weekday in [5, 6]:
        logger.info("Weekend détecté → pas de génération de séances.")
        return

    # Clé cache Redis
    cache_key = f"horaires_{today}"
    horaires_du_jour = cache.get(cache_key)

    if horaires_du_jour is None:
        logger.info("Cache vide → récupération des horaires depuis la DB.")
        jour_actuel = convertir_weekday_en_nom(weekday)

        horaires_qs = HoraireCours.objects.filter(jour_semaine=jour_actuel).order_by(
            "heure_debut"
        )

        # Sérialiser en dict pour Redis
        horaires_du_jour = [
            {
                "id": h.id,
                "cours": h.cours.nom,
                "classe_id": h.cours.classe.id,
                "heure_debut": h.heure_debut.strftime("%H:%M"),
                "heure_fin": h.heure_fin.strftime("%H:%M"),
            }
            for h in horaires_qs
        ]
        # Stocker en cache 5 minutes (300s)
        cache.set(cache_key, horaires_du_jour, timeout=300)
        logger.info(f"Horaires mis en cache ({len(horaires_du_jour)} horaires).")
    else:
        logger.info(
            f"Horaires récupérés depuis le cache ({len(horaires_du_jour)} horaires)."
        )

    # Créer les séances si elles n'existent pas encore et si l'heure de début est atteinte
    print("Horaires du jour :", horaires_du_jour)
    for horaire in horaires_du_jour:
        horaire_id = horaire["id"]
        classe_id = horaire["classe_id"]

        existe = SeanceCours.objects.filter(
            horaire_cours_id=horaire_id, date_seance=today
        ).exists()
        if existe:
            logger.debug(f"Séance déjà existante pour horaire {horaire_id} → ignorée.")
            continue

        # Vérifier si l'heure de début est atteinte
        heure_debut = datetime.strptime(horaire["heure_debut"], "%H:%M").time()
        if heure_debut <= now:
            try:
                seance = SeanceCours.objects.create(
                    horaire_cours_id=horaire_id,
                    date_seance=today,
                    heure_debut=heure_debut,
                    heure_fin=datetime.strptime(horaire["heure_fin"], "%H:%M").time(),
                    status="en_cours",  # Assure-toi que le champ 'status' existe dans SeanceCours
                )
                seance.save()
                logger.info(
                    f"Séance créée : {horaire['cours']} pour la classe {classe_id} "
                    f"({horaire['heure_debut']} - {horaire['heure_fin']})"
                )
            except Exception as e:
                logger.error(
                    f"Erreur lors de la création de la séance pour l'horaire {horaire_id} : {e}"
                )
            else:
                logger.debug(
                    f"Heure de début non atteinte pour l'horaire {horaire_id} → séance non créée."
                )


# --------------------------------------------------------------------------------


@shared_task
def task_verify_closed_seance():
    """
    Vérifie toutes les séances en cours et marque comme 'terminées' celles dont
    l'heure de fin est dépassée.
    """
    now = timezone.localtime()
    today = now.date()
    current_time = now.time()

    # Récupérer toutes les séances du jour dont l'heure de fin est dépassée
    seances_to_close = SeanceCours.objects.filter(
        date_seance=today, heure_fin__lte=current_time, status="en_cours"
    )

    if seances_to_close.exists():
        for seance in seances_to_close:
            # Ici, tu peux ajouter un champ 'status' à SeanceCoure si ce n'est pas encore fait
            seance.status = "termine"  # 'termine'
            seance.save()
            print(
                f"[TASK] Séance terminée : {seance.horaire_cours.cours.nom} ({seance.heure_debut}-{seance.heure_fin})"
            )


@shared_task
def send_seances_via_websocket():
    """
    Lit toutes les séances disponibles en cours du jour et les envoie au groupe 'seances_du_jour'.
    """
    now = timezone.localtime()
    today = now.date()

    seances_du_jour = SeanceCours.objects.filter(
        date_seance=today, status="en_cours"
    ).order_by("heure_debut")

    # Préparer les données à envoyer
    for seance in seances_du_jour:
        classe = seance.horaire_cours.cours.classe
        groupe = groupe_name(classe.id)

        # 1. Créer la structure de données pour cette SEANCE UNIQUE
        seance_data_payload = [  # On garde une liste pour la cohérence avec le format attendu par le client
            {
                "cours": seance.horaire_cours.cours.nom,
                "heure_debut": seance.heure_debut.strftime("%H:%M"),
                "heure_fin": seance.heure_fin.strftime("%H:%M"),
            }
        ]

        # 2. Envoyer immédiatement au groupe concerné
        channel_layer = get_channel_layer()

        async_to_sync(channel_layer.group_send)(
            groupe,
            {
                "type": "send_seances",
                "message": {
                    "date": str(today),
                    "seances": seance_data_payload,  # <-- N'envoie qu'une seule séance
                },
            },
        )
        print(
            f"[TASK] Envoi de la séance via WebSocket au groupe {groupe} : {seance_data_payload}"
        )
