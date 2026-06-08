from django.apps import AppConfig


class FinreportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finreports"

    def ready(self):
        from django.urls import include, path
        from horilla.horilla_settings import APP_URLS, APPS
        from horilla.urls import urlpatterns

        APPS.append("finreports")
        urlpatterns.append(
            path("finreports/", include("finreports.urls")),
        )
        APP_URLS.append("finreports.urls")
        super().ready()
