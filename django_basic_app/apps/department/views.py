"""Views for Department model CRUD operations."""

from typing import Any

from drf_easy_crud import CRUDUtils
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Department
from .serializers import DepartmentSerializer


class DepartmentListView(generics.ListCreateAPIView):
    """View for listing and creating Department instances."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a list of all Department instances."""
        return CRUDUtils.get(request=request, queryset=Department, serializer_class=DepartmentSerializer, **kwargs)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new Department instance."""
        return CRUDUtils.post(request=request, serializer_class=DepartmentSerializer)


class DepartmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting a single Department instance."""

    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific Department instance by primary key."""
        return CRUDUtils.get(request=request, queryset=Department, serializer_class=DepartmentSerializer, **kwargs)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fully update a Department instance by primary key."""
        return CRUDUtils.put(request=request, queryset=Department, serializer_class=DepartmentSerializer, **kwargs)

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partially update a Department instance by primary key."""
        return CRUDUtils.patch(request=request, queryset=Department, serializer_class=DepartmentSerializer, **kwargs)

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete a Department instance by primary key."""
        return CRUDUtils.delete(request=request, queryset=Department, **kwargs)
