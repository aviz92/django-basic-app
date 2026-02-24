from django_versioned_models.models import Release
from rest_framework import serializers

from ..department.models import Department
from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""

    name = serializers.CharField(max_length=255, required=True)

    release_version = serializers.SlugRelatedField(
        source="release",
        queryset=Release.objects.all(),
        slug_field="version",
        required=True,
        allow_null=True,
        help_text="Name of the related Release instance.",
    )
    department_name = serializers.SlugRelatedField(
        source="department",
        queryset=Department.objects.all(),
        slug_field="name",
        required=False,
        allow_null=True,
        help_text="Name of the related Department instance (optional).",
    )

    class Meta:
        model = Employee
        fields = "__all__"
        depth = 10
