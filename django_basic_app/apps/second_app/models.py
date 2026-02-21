from apps.core.mixins import VersionedModel
from apps.first_app.models import FirstApp
from django.db import models


class SecondApp(VersionedModel):
    # Basic fields
    created_at = models.DateTimeField(verbose_name="Created at", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated at", auto_now=True)
    name = models.CharField(verbose_name="Name", max_length=255, blank=False, unique=True)
    description = models.TextField(verbose_name="Description", null=True, blank=True)

    first_app = models.ForeignKey(FirstApp, verbose_name="first_app", on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        unique_together = [('release', 'name')]

    def __str__(self) -> str:
        return self.name
