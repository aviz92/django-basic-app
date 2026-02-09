from rest_framework import serializers

from ..first_app.models import FirstApp
from .models import SecondApp


class SecondAppSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    first_app_name = serializers.SlugRelatedField(
        source="first_app",
        queryset=FirstApp.objects.all(),
        slug_field="name",
        required=False,
        allow_null=True,
        help_text="name of the related FirstApp instance (optional)",
    )

    class Meta:
        model = SecondApp
        fields = "__all__"

        depth = 10
