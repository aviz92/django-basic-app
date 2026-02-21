from django_versioned_models.models import Release
from rest_framework import serializers

from ..employee.models import Employee
from .models import Department


class DepartmentSerializer(serializers.ModelSerializer):
    """Serializer for Department model."""

    name = serializers.CharField(max_length=255, required=True)

    release_version = serializers.SlugRelatedField(
        source="release",
        queryset=Release.objects.all(),
        slug_field="version",
        required=True,
        allow_null=True,
        help_text="Name of the related Release instance.",
    )
    employee_name = serializers.SlugRelatedField(
        source="employee",
        queryset=Employee.objects.all(),
        slug_field="name",
        required=False,
        allow_null=True,
        help_text="Name of the related Employee instance (optional).",
    )

    class Meta:
        model = Department
        fields = "__all__"
        depth = 10
