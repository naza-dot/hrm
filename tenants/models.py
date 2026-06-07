import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _


class Client(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("Company Name"))
    schema_name = models.CharField(max_length=63, unique=True)
    company = models.ForeignKey(
        "base.Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="clients",
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("creating", _("Creating")),
            ("active", _("Active")),
            ("failed", _("Failed")),
        ],
        default="pending",
    )
    progress = models.IntegerField(default=0, help_text=_("Schema creation progress 0-100"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Client")
        verbose_name_plural = _("Clients")

    def __str__(self):
        return self.name
