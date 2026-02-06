from rest_framework import serializers

from .models import SecondApp


class SecondAppSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = SecondApp
        fields = '__all__'

        depth = 10
