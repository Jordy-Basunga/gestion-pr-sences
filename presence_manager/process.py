from datetime import date, datetime

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
        existe = SeanceCoure.objects.filter(
            horaire_cours=horaire, date_seance=today
        ).exists()

        if existe:
            continue  # passe au cours suivant

        # Vérifier si l'heure de début est atteinte
        if horaire.heure_debut <= now:
            # Créer la séance
            SeanceCoure.objects.create(
                horaire_cours=horaire,
                date_seance=today,
                heure_debut=horaire.heure_debut,
                heure_fin=horaire.heure_fin,
            )
