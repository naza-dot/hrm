from django.apps import AppConfig


class FinanceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "finance"

    def ready(self):
        from django.urls import include, path
        from horilla.horilla_settings import APP_URLS, APPS
        from horilla.urls import urlpatterns

        APPS.append("finance")
        urlpatterns.append(
            path("finance/", include("finance.urls")),
        )
        APP_URLS.append("finance.urls")
        super().ready()
