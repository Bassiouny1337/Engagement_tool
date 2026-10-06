from django.apps import AppConfig


class EngagementsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.engagements"
    label = "engagements"

    def ready(self):
        from . import signals  # noqa: F401
