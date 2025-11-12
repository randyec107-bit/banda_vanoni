
from django.apps import AppConfig

class AdquisicionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'adquisiciones'
    
    def ready(self):

        import adquisiciones.signals