from rest_framework import serializers

from django_versioned_models.models import Release

from .models import Employee


class EmployeeSerializer(serializers.ModelSerializer):
    """Serializer for Employee model."""

    name = serializers.CharField(max_length=255, required=True)
    release = serializers.PrimaryKeyRelatedField(
        queryset=Release.objects.all(),
        required=True,
    )

    class Meta:
        model = Employee
        fields = "__all__"
        depth = 10
