from django.apps import AppConfig


class PresenceManagerConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presence_manager"


from django.apps import AppConfig


class PresenceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "presence_manager"

    def ready(self):
        from .tasks import start_presence_scheduler

        start_presence_scheduler()
