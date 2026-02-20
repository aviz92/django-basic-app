"""
apps/core/mixins.py

VersionedModel is the only thing every app model needs to inherit.
It adds:
  1. FK to Release              — which version does this row belong to?
  2. Lock enforcement           — locked releases cannot be edited
  3. objects manager            — always scoped to a release
"""
from django.db import models
from django.core.exceptions import ValidationError


class VersionedModel(models.Model):
    """
    Abstract base for every versioned entity.

    Usage:
        class Product(VersionedModel):
            sku = models.CharField(...)
            ...

    Querying a specific version:
        Product.objects.for_release(release)

    The save() method enforces immutability:
        - Existing rows in a locked release → raises ValidationError
        - New rows into a locked release    → raises ValidationError
    """

    release = models.ForeignKey(
        'core.Release',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
    )

    class VersionedManager(models.Manager):
        def for_release(self, release):
            return self.get_queryset().filter(release=release)

    objects = VersionedManager()

    def save(self, *args, **kwargs):
        # Enforce immutability on locked releases
        if self.release.is_locked:
            raise ValidationError(
                f'Release {self.release.version} is locked and cannot be modified. '
                f'Create a new release (patch) instead.'
            )
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.release.is_locked:
            raise ValidationError(
                f'Release {self.release.version} is locked. Cannot delete rows.'
            )
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True
