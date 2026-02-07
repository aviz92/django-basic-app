from django.contrib import admin

from .models import SecondApp


@admin.register(SecondApp)
class SecondAppAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at", "name")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")
    save_on_top = True
    fieldsets = (
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        ("Basic Info", {"fields": ("name",)}),
        ("Relations", {"fields": ("first_app",)}),
    )
