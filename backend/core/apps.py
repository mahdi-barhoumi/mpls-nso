from django.apps import AppConfig
from django.db.models import Q

import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="django.db.backends.utils")

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'core'

    def ready(self):
        # Import here to avoid AppRegistryNotReady error
        from django.contrib.auth.models import User
        from core.settings import Settings

        # Set global state
        self.state = {
            'has_admin': User.objects.filter(Q(is_superuser=True) | Q(is_staff=True)).exists(),
            'has_settings': Settings.objects.exists()
        }