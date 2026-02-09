from rest_framework import serializers

from ..first_app.models import FirstApp
from .models import SecondApp


class SecondAppSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)

    # _name is added to fetch the nested object via api call and avoid conflict with the actual 'name' field of
    # SecondApp and to make it clear that this field is related to the FirstApp model slug_field="name".
    # The source="first_app" tells the serializer to use the 'first_app' relationship to fetch the related FirstApp
    # instance based on the provided slug value.
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
