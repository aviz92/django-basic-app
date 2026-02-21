from django.contrib import admin

from .models import Department


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at", "name")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")
    save_on_top = True
    fieldsets = (
        ("Timestamps", {"fields": ("created_at", "updated_at")}),
        (
            "Basic Info",
            {
                "fields": (
                    "release",
                    "status",
                    "name",
                )
            },
        ),
        ("Relations", {"fields": ("employee",)}),
    )
