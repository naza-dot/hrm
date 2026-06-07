from django.contrib import admin

from tenants.models import Client


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["name", "schema_name", "status", "progress", "created_at"]
    list_filter = ["status"]
