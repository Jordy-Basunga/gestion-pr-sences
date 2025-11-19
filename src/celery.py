import os
from celery import Celery


# ici nous définissons la variable d'environnement pour le module de paramètres Django
# nécessaire pour que Celery puisse accéder aux configurations de Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.settings")
app = Celery("src")
app.config_from_object("django.conf:settings", namespace="CELERY")


"""
ce fichier configure Celery pour l'application Django. Il définit le broker Redis pour la gestion des tâches asynchrones
et programme une tâche périodique qui s'exécute toutes les 5 secondes.
il utilise le module de configuration de Django pour charger les paramètres Celery.
app.conf.beat_schedule définit une tâche planifiée nommée "run-every-30-seconds" qui exécute la tâche "presence_manager.tasks.run_tasks" toutes les 5 secondes.


"""
app.conf.beat_schedule = {
    # "run-every-30-seconds": {
    #     "task": "presence_manager.tasks.run_tasks",
    #     "schedule": 10.0,
    # },
    "run-every-1-minute": {
        "task": "presence_manager.tasks.generer_seances_du_jour",
        "schedule": 15.0,
    },
    "run-every-1-second": {
        "task": "presence_manager.tasks.task_verify_closed_seance",
        "schedule": 1.0,
    },
    "run-every-10-second": {
        "task": "presence_manager.tasks.send_seances_via_websocket",
        "schedule": 10.0,
    },
}

# ici nous autodécouvrons les tâches dans les applications installées de Django
# cela permet à Celery de trouver automatiquement les tâches définies dans les fichiers tasks.py des applications
app.autodiscover_tasks()
