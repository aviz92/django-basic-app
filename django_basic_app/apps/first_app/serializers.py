from rest_framework import serializers

from .models import FirstApp


class FirstAppSerializer(serializers.ModelSerializer):
    name = serializers.CharField(max_length=255, required=True)

    class Meta:
        model = FirstApp
        fields = '__all__'

        depth = 10
