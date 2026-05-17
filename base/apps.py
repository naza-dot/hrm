"""Application configuration for the ``base`` app.

The project historically used a custom ``ready`` hook to create the
``MicrosoftSSOConfig`` table via raw SQL.  The current migration strategy
creates the table through a normal Django migration, so the hook is no
longer required.  The ``BaseConfig`` below simply declares the app name
and default auto‑field.
"""

from django.apps import AppConfig


class BaseConfig(AppConfig):
    """Configuration for the ``base`` Django app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "base"
    verbose_name = "Base"
