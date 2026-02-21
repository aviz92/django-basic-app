"""
apps/core/mixins.py

VersionedModel is the only thing every app model needs to inherit.
It adds:
  1. FK to Release              — which version does this row belong to?
  2. Status                     — data readiness (draft / future / approved)
  3. Lock enforcement           — locked releases cannot be edited
  4. objects manager            — scoped queries by release and status

Status flow:
    DRAFT <-> FUTURE -> APPROVED  (APPROVED is one-way, CI only)

CI runs against: status=APPROVED
Architects edit: status=DRAFT or FUTURE
"""
from django.db import models
from django.core.exceptions import ValidationError


class DataStatus(models.TextChoices):
    DRAFT = ('draft', 'Draft')
    FUTURE = ('future', 'Future')
    APPROVED = ('approved', 'Approved')


class VersionedModel(models.Model):
    """
    Abstract base for every versioned entity.

    Usage:
        class Product(VersionedModel):
            sku = models.CharField(...)

    Querying by release and status:
        Product.objects.for_release(release)               # all statuses
        Product.objects.approved(release)                  # CI uses this
        Product.objects.filter(release=r, status='future') # future pipeline
    """

    release = models.ForeignKey(
        'core.Release',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
    )
    status = models.CharField(
        max_length=20,
        choices=DataStatus,
        default=DataStatus.DRAFT,
        db_index=True,
    )

    # ── Manager ───────────────────────────────────────────────────────────────

    class VersionedManager(models.Manager):

        def for_release(self, release):
            """All rows for a release, regardless of status."""
            return self.get_queryset().filter(release=release)

        def approved(self, release):
            """Only approved rows — what CI runs against."""
            return self.get_queryset().filter(
                release=release,
                status=DataStatus.APPROVED,
            )

    objects = VersionedManager()

    # ── Status transitions ────────────────────────────────────────────────────

    def mark_future(self):
        """DRAFT → FUTURE. Called by architects."""
        if self.status != DataStatus.DRAFT:
            raise ValidationError(
                f'Can only move to FUTURE from DRAFT. Current status: {self.status}'
            )
        self.status = DataStatus.FUTURE
        self.save(update_fields=['status'])

    def mark_draft(self):
        """FUTURE → DRAFT. Allows rework."""
        if self.status != DataStatus.FUTURE:
            raise ValidationError(
                f'Can only move back to DRAFT from FUTURE. Current status: {self.status}'
            )
        self.status = DataStatus.DRAFT
        self.save(update_fields=['status'])

    def approve(self):
        """
        DRAFT → APPROVED or FUTURE → APPROVED.
        One-way. Called by CI only.
        """
        if self.status == DataStatus.APPROVED:
            raise ValidationError('Row is already approved.')
        self.status = DataStatus.APPROVED
        self.save(update_fields=['status'])

    # ── Lock enforcement ──────────────────────────────────────────────────────

    def save(self, *args, **kwargs):
        if self.release.is_locked and self.status != DataStatus.APPROVED:
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
