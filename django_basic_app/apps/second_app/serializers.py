from rest_framework import serializers

from .models import SecondApp
from ..first_app.models import FirstApp


class SecondAppSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)
    first_app = serializers.SlugRelatedField(
        queryset=FirstApp.objects.all(),
        slug_field='name',
        required=False,
        allow_null=True,
        help_text='name of the related FirstApp instance (optional)'
    )

    class Meta:
        model = SecondApp
        fields = '__all__'

        depth = 10
