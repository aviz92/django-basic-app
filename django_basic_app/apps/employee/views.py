"""Views for Employee model CRUD operations."""

from typing import Any

from drf_easy_crud import CRUDUtils
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Employee
from .serializers import EmployeeSerializer


class EmployeeListView(generics.ListCreateAPIView):
    """View for listing and creating Employee instances."""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a list of all Employee instances."""
        return CRUDUtils.get(request=request, queryset=Employee, serializer_class=EmployeeSerializer, **kwargs)

    def post(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Create a new Employee instance."""
        return CRUDUtils.post(request=request, serializer_class=EmployeeSerializer)


class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for retrieving, updating, and deleting a single Employee instance."""

    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Retrieve a specific Employee instance by primary key."""
        return CRUDUtils.get(request=request, queryset=Employee, serializer_class=EmployeeSerializer, **kwargs)

    def put(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Fully update an Employee instance by primary key."""
        return CRUDUtils.put(request=request, queryset=Employee, serializer_class=EmployeeSerializer, **kwargs)

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Partially update an Employee instance by primary key."""
        return CRUDUtils.patch(request=request, queryset=Employee, serializer_class=EmployeeSerializer, **kwargs)

    def delete(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Delete an Employee instance by primary key."""
        return CRUDUtils.delete(request=request, queryset=Employee, **kwargs)
