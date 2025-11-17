import os
from apscheduler.schedulers.background import BackgroundScheduler
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime, date
from presence_manager.models import HoraireCours, SeanceCoure

from apscheduler.schedulers.background import BackgroundScheduler
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json


def Cstart_presence_scheduler():
    scheduler = BackgroundScheduler()
    iteration = {"count": 0}

    def send_message():
        iteration["count"] += 1
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "presence_group",
            {
                "type": "send_presence_message",
                "message": {"message": f"debut premier cours {iteration['count']}"},
            },
        )
        print(f"[Scheduler] Message envoyé: iteration {iteration['count']}")

    scheduler.add_job(send_message, "interval", seconds=2)
    scheduler.start()


def generer_seances_du_jour():
    jour_systeme = datetime.today().strftime("%A").upper()

    mapping = {
        "MONDAY": "LUNDI",
        "TUESDAY": "MARDI",
        "WEDNESDAY": "MERCREDI",
        "THURSDAY": "JEUDI",
        "FRIDAY": "VENDREDI",
        "SATURDAY": "SAMEDI",
        "SUNDAY": "DIMANCHE",
    }

    jour = mapping[jour_systeme]
    horaires = HoraireCours.objects.filter(jour_semaine=jour)
    channel_layer = get_channel_layer()

    for horaire in horaires:
        deja = SeanceCoure.objects.filter(
            horaire_cours=horaire, date_seance=date.today()
        ).exists()

        if deja:
            continue

        seance = SeanceCoure.objects.create(
            horaire_cours=horaire,
            date_seance=date.today(),
            heure_debut=horaire.heure_debut,
            heure_fin=horaire.heure_fin,
        )

        async_to_sync(channel_layer.group_send)(
            "seances_du_jour",
            {
                "type": "nouvelle_seance",
                "message": {
                    "cours": horaire.cours.nom,
                    "date": str(seance.date_seance),
                    "heure_debut": str(seance.heure_debut),
                    "heure_fin": str(seance.heure_fin),
                },
            },
        )


def start_presence_scheduler():
    # Empêche le scheduler de tourner deux fois (cause : autoreload)
    if os.environ.get("RUN_MAIN") != "true":
        return

    scheduler = BackgroundScheduler()
    scheduler.add_job(generer_seances_du_jour, "interval", minutes=1)
    scheduler.start()

    print("[Scheduler] Démarré (génère les séances du jour chaque minute)")
