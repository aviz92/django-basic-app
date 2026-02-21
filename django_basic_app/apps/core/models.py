"""
apps/core/models.py

Release is the backbone of the entire versioning system.

Every data row in every app has a FK to Release.
When a new release is created (via CI), all rows from the previous
release are copied into the new one — architects then modify the copy.

A locked release is immutable. Patches create a new release (branched
from the patched version), never modify the existing one.

A deprecated release is hidden from the GUI and API by default.
Data is preserved — nothing is deleted.
"""

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Release(models.Model):
    version = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    based_on = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="children",
        help_text="Which release was this branched from?",
    )
    is_locked = models.BooleanField(
        default=False,
        help_text="Locked releases are immutable. Set by CI on release.",
    )
    is_deprecated = models.BooleanField(
        default=False,
        help_text="Deprecated releases are hidden by default. Data is preserved.",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    locked_at = models.DateTimeField(null=True, blank=True)
    deprecated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        if self.is_deprecated:
            status = "🗄️️"
        elif self.is_locked:
            status = "🔒"
        else:
            status = "✏️"
        return f"{status} {self.version}"

    def lock(self) -> None:
        self.is_locked = True
        self.locked_at = timezone.now()
        self.save(update_fields=["is_locked", "locked_at"])

    def deprecate(self) -> None:
        self.is_deprecated = True
        self.deprecated_at = timezone.now()
        self.save(update_fields=["is_deprecated", "deprecated_at"])

    def undeprecate(self) -> None:
        self.is_deprecated = False
        self.deprecated_at = None
        self.save(update_fields=["is_deprecated", "deprecated_at"])
