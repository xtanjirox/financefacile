from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        import core.forms  # Ensures django-select2 widgets are registered
        import core.signals  # Import signals to register them
        import core.notifications  # Import notifications model
