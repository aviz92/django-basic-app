from django.db import models
from django_versioned_models.mixins import VersionedModel

from apps.employee.models import Employee


class Department(VersionedModel):
    """Department model (versioned), related to Employee."""

    created_at = models.DateTimeField(verbose_name="Created at", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated at", auto_now=True)
    name = models.CharField(verbose_name="Name", max_length=255, blank=False)
    description = models.TextField(verbose_name="Description", null=True, blank=True)

    employee = models.ForeignKey(
        Employee, verbose_name="employee", on_delete=models.CASCADE, null=True, blank=True
    )

    class Meta:
        unique_together = [("release", "name")]

    def __str__(self) -> str:
        return self.name
