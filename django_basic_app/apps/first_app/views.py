from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from django_basic_app.view_functions import ViewFunctions

from .models import FirstApp
from .serializers import FirstAppSerializer


class FirstAppView(generics.ListCreateAPIView):
    queryset = FirstApp.objects.all()
    serializer_class = FirstAppSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    # permission_classes = (AllowAny,)

    def get(self, request, *args, **kwargs):
        return ViewFunctions().get(
            request=request,
            model_class=FirstApp,
            model_serializer_class=FirstAppSerializer,
            **kwargs
        )

    def post(self, request, *args, **kwargs):
        return ViewFunctions().post(
            request=request,
            model_serializer_set_class=FirstAppSerializer
        )
