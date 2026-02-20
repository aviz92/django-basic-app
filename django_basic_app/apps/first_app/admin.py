from django.contrib import admin

from .models import FirstApp


@admin.register(FirstApp)
class FirstAppAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at", "name")
    search_fields = ("name",)
    readonly_fields = ("id", "created_at", "updated_at")
    save_on_top = True
    fieldsets = (("Basic Info", {"fields": ("release", "name",)}),)
