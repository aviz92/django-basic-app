"""Comprehensive tests for CRUDUtils class."""

import json

# Import from django_basic_app - need to add it to path first
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from drf_easy_crud import CRUDUtils, FilterUtils
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import JSONParser
from rest_framework.request import Request as DRFRequest
from rest_framework.test import APIRequestFactory

# Add django_basic_app to path
project_root = Path(__file__).resolve().parent.parent
django_basic_app_path = project_root / "django_basic_app"
if str(django_basic_app_path) not in sys.path:
    sys.path.insert(0, str(django_basic_app_path))

from apps.department.models import Department
from apps.department.serializers import DepartmentSerializer
from apps.employee.models import Employee
from apps.employee.serializers import EmployeeSerializer
from django_versioned_models.models import Release

User = get_user_model()


def _release() -> Release:
    """Create a test release (unlocked) for versioned models."""
    release, _ = Release.objects.get_or_create(
        version="test-release",
        defaults={"description": "Test release", "is_locked": False},
    )
    return release


factory = APIRequestFactory()


def _make_authenticated_request(
    method: str = "GET",
    path: str = "/",
    data: dict | None = None,
    query_params: dict | None = None,
    token: Token | None = None,
) -> DRFRequest:
    """Helper to create authenticated DRF request."""

    if method == "GET":
        request = factory.get(path, query_params or {})
    elif method == "POST":
        request = factory.post(path, json.dumps(data or {}), content_type="application/json")
    elif method == "PUT":
        request = factory.put(path, json.dumps(data or {}), content_type="application/json")
    elif method == "PATCH":
        request = factory.patch(path, json.dumps(data or {}), content_type="application/json")
    elif method == "DELETE":
        request = factory.delete(path)
    else:
        request = factory.get(path)

    if token:
        request.META["HTTP_AUTHORIZATION"] = f"Token {token.key}"

    # Create DRF Request with parser for JSON data
    drf_request = DRFRequest(request)
    # Set parsers explicitly for JSON requests
    if method in {"POST", "PUT", "PATCH"}:
        drf_request.parsers = [JSONParser()]

    return drf_request


class TestCRUDUtilsGet(TestCase):
    """Test CRUDUtils.get() method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.release = _release()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.token = Token.objects.create(user=self.user)

        # Create test instances
        self.employee_instances = [
            Employee.objects.create(name="test1", description="Description 1", release=self.release),
            Employee.objects.create(name="test2", description="Description 2", release=self.release),
            Employee.objects.create(name="product1", description="Product description", release=self.release),
            Employee.objects.create(name="other", description="Other description", release=self.release),
        ]

    def test_get_single_instance(self) -> None:
        """Test retrieving a single instance by PK."""
        request = _make_authenticated_request("GET", f"/employee/{self.employee_instances[0].pk}/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Employee,
            serializer_class=EmployeeSerializer,
            pk=self.employee_instances[0].pk,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.employee_instances[0].pk)
        self.assertEqual(response.data["name"], "test1")

    def test_get_single_instance_not_found(self) -> None:
        """Test retrieving non-existent instance returns 404."""
        request = _make_authenticated_request("GET", "/employee/999/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Employee,
            serializer_class=EmployeeSerializer,
            pk=999,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_list_without_filters(self) -> None:
        """Test retrieving list without filters."""
        request = _make_authenticated_request("GET", "/employee/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Employee,
            serializer_class=EmployeeSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 4)

    def test_get_list_with_text_wildcard_starts_with(self) -> None:
        """Test filtering with wildcard pattern: starts with."""
        request = _make_authenticated_request("GET", "/employee/", query_params={"name": "test*"}, token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Employee,
            serializer_class=EmployeeSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all("test" in item["name"].lower() for item in results))

    def test_get_list_with_text_wildcard_contains(self) -> None:
        """Test filtering with wildcard pattern: contains."""
        request = _make_authenticated_request("GET", "/employee/", query_params={"name": "*test*"}, token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Employee,
            serializer_class=EmployeeSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all("test" in item["name"].lower() for item in results))

    def test_validation_error_nonexistent_field(self) -> None:
        """Test filtering with non-existent field returns empty results."""
        with pytest.raises(ValidationError):
            request = _make_authenticated_request(
                "GET", "/employee/", query_params={"nonexistent": "value"}, token=self.token
            )
            _ = CRUDUtils.get(
                request=request,
                queryset=Employee,
                serializer_class=EmployeeSerializer,
            )

    def test_get_list_with_foreignkey_lookup(self) -> None:
        """Test filtering Department list by department name."""
        dept1 = Department.objects.create(name="dept1", release=self.release)
        dept2 = Department.objects.create(name="dept2", release=self.release)
        self.employee_instances[0].department = dept1
        self.employee_instances[0].save()
        self.employee_instances[1].department = dept2
        self.employee_instances[1].save()

        request = _make_authenticated_request("GET", "/department/", query_params={"name": "dept1"}, token=self.token)
        response = CRUDUtils.get(
            request=request,
            queryset=Department,
            serializer_class=DepartmentSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "dept1")


class TestCRUDUtilsPost(TestCase):
    """Test CRUDUtils.post() method."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.release = _release()
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        self.token = Token.objects.create(user=self.user)

    def test_post_create_instance(self) -> None:
        """Test creating a new instance."""
        request = _make_authenticated_request(
            "POST",
            "/employee/",
            data={
                "name": "New Item",
                "description": "New Description",
                "release_version": self.release.version,
            },
            token=self.token,
        )
        response = CRUDUtils.post(
            request=request,
            serializer_class=EmployeeSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Item")
        self.assertTrue(Employee.objects.filter(name="New Item").exists())

    def test_post_validation_error(self) -> None:
        """Test creating instance with validation error."""
        request = _make_authenticated_request(
            "POST", "/employee/", data={"description": "Missing name"}, token=self.token
        )
        response = CRUDUtils.post(
            request=request,
            serializer_class=EmployeeSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)


class TestCRUDUtilsHelperMethods(TestCase):
    """Test helper methods."""

    def test_has_middle_wildcard(self) -> None:
        """Test detecting middle wildcard."""
        self.assertTrue(FilterUtils._has_middle_wildcard("t*t"))  # pylint: disable=W0212
        self.assertFalse(FilterUtils._has_middle_wildcard("test*"))  # pylint: disable=W0212
        self.assertFalse(FilterUtils._has_middle_wildcard("*test"))  # pylint: disable=W0212
        self.assertFalse(FilterUtils._has_middle_wildcard("*test*"))  # pylint: disable=W0212

    def test_wildcard_to_regex(self) -> None:
        """Test wildcard to regex conversion."""
        regex = FilterUtils._wildcard_to_regex("t*t")  # pylint: disable=W0212
        self.assertIn(".*", regex)
        self.assertTrue(regex.startswith("t"))
        self.assertTrue(regex.endswith("t"))
