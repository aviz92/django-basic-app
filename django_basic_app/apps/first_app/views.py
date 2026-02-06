"""Views for FirstApp model CRUD operations."""

from typing import Any

from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from django_basic_app.crud_utils import CRUDUtils

from .models import FirstApp
from .serializers import FirstAppSerializer


class FirstAppListView(generics.ListCreateAPIView):
    """View for listing and creating FirstApp instances.

    Supports:
    - GET /first_app/ - List all instances
    - POST /first_app/ - Create a new instance
    """

    queryset = FirstApp.objects.all()
    serializer_class = FirstAppSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a list of all FirstApp instances."""
        return CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            **kwargs
        )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new FirstApp instance."""
        return CRUDUtils.post(
            request=request,
            serializer_class=FirstAppSerializer
        )


class FirstAppDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting a single FirstApp instance.

    Supports:
    - GET /first_app/<pk>/ - Retrieve a specific instance
    - PUT /first_app/<pk>/ - Full update of an instance
    - PATCH /first_app/<pk>/ - Partial update of an instance
    - DELETE /first_app/<pk>/ - Delete an instance
    """

    queryset = FirstApp.objects.all()
    serializer_class = FirstAppSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific FirstApp instance by primary key."""
        return CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            **kwargs
        )

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fully update a FirstApp instance by primary key."""
        return CRUDUtils.put(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            **kwargs
        )

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partially update a FirstApp instance by primary key."""
        return CRUDUtils.patch(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            **kwargs
        )

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a FirstApp instance by primary key."""
        return CRUDUtils.delete(
            request=request,
            model_class=FirstApp,
            **kwargs
        )