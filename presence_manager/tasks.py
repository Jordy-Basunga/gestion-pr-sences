from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def run_tasks():
    # print("Running scheduled tasks...")
    # logger.info("Running scheduled tasks...")
    pass


from datetime import date, datetime
from presence_manager.models import *
from .utils import convertir_weekday_en_nom
from .models import HoraireCours, SeanceCoure
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
    print(f"[Tâche] Heure actuelle : {now}")
    weekday = today.weekday()  # 0 = Lundi, ..., 6 = Dimanche
    print(f"[Tâche] Génération des séances pour le jour {today} (weekday={weekday})")
    # Étape 1 : Vérifier si c'est un week-end
    if weekday in [5, 6]:
        return  # Samedi ou dimanche → rien à générer

    # Étape 2 : Récupérer les horaires du jour
    jour_actuel = convertir_weekday_en_nom(weekday)
    print(f"[Tâche] Jour actuel : {jour_actuel}")
    horaires_du_jour = HoraireCours.objects.filter(jour_semaine=jour_actuel).order_by(
        "heure_debut"
    )
    print(f"[Tâche] Horaires trouvés pour {jour_actuel} : {horaires_du_jour}")
    print(f"[Tâche] jour actuelle : {today}")
    # Étape 3 : Vérifier et créer les séances
    for horaire in horaires_du_jour:
        print("[Tâche] Traitement de l'horaire :", {today}, "cool")
        # Vérifier si la séance existe déjà pour aujourd'hui
        existe = SeanceCoure.objects.filter(
            horaire_cours=horaire, date_seance=today
        ).exists()

        if existe:
            print("[Tâche] La séance existe déjà pour l'horaire :", horaire)
            continue  # passe au cours suivant
        else:
            print("[Tâche] La séance n'existe pas encore pour l'horaire :", horaire)

        # Vérifier si l'heure de début est atteinte
        print("[Tâche] Vérification de l'heure pour l'horaire :", horaire)
        if horaire.heure_debut <= now:
            # Créer la séance
            seance = SeanceCoure.objects.create(
                horaire_cours=horaire,
                date_seance=today,
                heure_debut=horaire.heure_debut,
                heure_fin=horaire.heure_fin,
            )
            logger.info(
                f"Séance créée: {seance.horaire_cours.cours.nom} le {seance.date_seance} de {seance.heure_debut} à {seance.heure_fin}"
            )
            seance.save()


from celery import shared_task
from django.utils import timezone
from presence_manager.models import SeanceCoure


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
    seances_to_close = SeanceCoure.objects.filter(
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


# presence_manager/tasks.py
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from presence_manager.models import SeanceCoure


@shared_task
def send_seances_via_websocket():
    """
    Lit toutes les séances disponibles en cours du jour et les envoie au groupe 'seances_du_jour'.
    """
    now = timezone.localtime()
    today = now.date()

    seances_du_jour = SeanceCoure.objects.filter(
        date_seance=today, status="en_cours"
    ).order_by("heure_debut")

    # Préparer les données à envoyer
    data = []
    for seance in seances_du_jour:
        data.append(
            {
                "cours": seance.horaire_cours.cours.nom,
                "heure_debut": seance.heure_debut.strftime("%H:%M"),
                "heure_fin": seance.heure_fin.strftime("%H:%M"),
            }
        )

    # Récupérer le layer de channels
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "seances_du_jour",
        {
            "type": "send_seances",
            "message": {
                "date": str(today),
                "seances": data,
            },
        },
    )
