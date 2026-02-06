"""Views for SecondApp model CRUD operations."""

from typing import Any

from drf_easy_crud import CRUDUtils
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import SecondApp
from .serializers import SecondAppSerializer


class SecondAppListView(generics.ListCreateAPIView):
    """View for listing and creating SecondApp instances.

    Supports:
    - GET /first_app/ - List all instances
    - POST /first_app/ - Create a new instance
    """

    queryset = SecondApp.objects.all()
    serializer_class = SecondAppSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a list of all SecondApp instances."""
        return CRUDUtils.get(
            request=request,
            model_class=SecondApp,
            serializer_class=SecondAppSerializer,
            **kwargs
        )

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new SecondApp instance."""
        return CRUDUtils.post(
            request=request,
            serializer_class=SecondAppSerializer
        )


class SecondAppDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting a single SecondApp instance.

    Supports:
    - GET /first_app/<pk>/ - Retrieve a specific instance
    - PUT /first_app/<pk>/ - Full update of an instance
    - PATCH /first_app/<pk>/ - Partial update of an instance
    - DELETE /first_app/<pk>/ - Delete an instance
    """

    queryset = SecondApp.objects.all()
    serializer_class = SecondAppSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific SecondApp instance by primary key."""
        return CRUDUtils.get(
            request=request,
            model_class=SecondApp,
            serializer_class=SecondAppSerializer,
            **kwargs
        )

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fully update a SecondApp instance by primary key."""
        return CRUDUtils.put(
            request=request,
            model_class=SecondApp,
            serializer_class=SecondAppSerializer,
            **kwargs
        )

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partially update a SecondApp instance by primary key."""
        return CRUDUtils.patch(
            request=request,
            model_class=SecondApp,
            serializer_class=SecondAppSerializer,
            **kwargs
        )

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a SecondApp instance by primary key."""
        return CRUDUtils.delete(
            request=request,
            model_class=SecondApp,
            **kwargs
        )
