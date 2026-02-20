from django.db import models
from apps.core.mixins import VersionedModel


class Category(VersionedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = [('release', 'name')]

    def __str__(self):
        return self.name


class Product(VersionedModel):
    sku = models.CharField(max_length=50)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [('release', 'sku')]
        ordering = ['sku']

    def __str__(self):
        return f'{self.sku} - {self.name}'
