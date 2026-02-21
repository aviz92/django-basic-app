from apps.core.mixins import VersionedModel
from django.db import models


class Category(VersionedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [("release", "name")]

    def __str__(self) -> str:
        return self.name


class Product(VersionedModel):
    created_at = models.DateTimeField(verbose_name="Created at", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="Updated at", auto_now=True)
    name = models.CharField(verbose_name="Name", max_length=255, blank=False)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("release", "name")]
        # ordering = ['name']

    def __str__(self) -> str:
        return self.name
