"""Comprehensive tests for CRUDUtils class."""

# Import from django_basic_app - need to add it to path first
import sys
from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.test import TestCase
from drf_easy_crud import CRUDUtils, FilterUtils
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

# Add django_basic_app to path
project_root = Path(__file__).resolve().parent.parent
django_basic_app_path = project_root / "django_basic_app"
if str(django_basic_app_path) not in sys.path:
    sys.path.insert(0, str(django_basic_app_path))

from apps.first_app.models import FirstApp
from apps.first_app.serializers import FirstAppSerializer
from apps.second_app.models import SecondApp
from apps.second_app.serializers import SecondAppSerializer

User = get_user_model()
factory = APIRequestFactory()


def _make_authenticated_request(method="GET", path="/", data=None, query_params=None, token=None):
    """Helper to create authenticated DRF request."""
    import json

    from rest_framework.parsers import JSONParser
    from rest_framework.request import Request as DRFRequest

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
    if method in ["POST", "PUT", "PATCH"]:
        drf_request.parsers = [JSONParser()]

    return drf_request


class TestCRUDUtilsGet(TestCase):
    """Test CRUDUtils.get() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        from rest_framework.authtoken.models import Token

        self.token = Token.objects.create(user=self.user)

        # Create test instances
        self.first_app_instances = [
            FirstApp.objects.create(name="test1", description="Description 1"),
            FirstApp.objects.create(name="test2", description="Description 2"),
            FirstApp.objects.create(name="product1", description="Product description"),
            FirstApp.objects.create(name="other", description="Other description"),
        ]

    def test_get_single_instance(self):
        """Test retrieving a single instance by PK."""
        request = _make_authenticated_request("GET", f"/first_app/{self.first_app_instances[0].pk}/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            pk=self.first_app_instances[0].pk,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.first_app_instances[0].pk)
        self.assertEqual(response.data["name"], "test1")

    def test_get_single_instance_not_found(self):
        """Test retrieving non-existent instance returns 404."""
        request = _make_authenticated_request("GET", "/first_app/999/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
            pk=999,
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_list_without_filters(self):
        """Test retrieving list without filters."""
        request = _make_authenticated_request("GET", "/first_app/", token=self.token)
        response = CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 4)

    def test_get_list_with_text_wildcard_starts_with(self):
        """Test filtering with wildcard pattern: starts with."""
        request = _make_authenticated_request("GET", "/first_app/", query_params={"name": "test*"}, token=self.token)
        response = CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all("test" in item["name"].lower() for item in results))

    def test_get_list_with_text_wildcard_contains(self):
        """Test filtering with wildcard pattern: contains."""
        request = _make_authenticated_request("GET", "/first_app/", query_params={"name": "*test*"}, token=self.token)
        response = CRUDUtils.get(
            request=request,
            model_class=FirstApp,
            serializer_class=FirstAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 2)
        self.assertTrue(all("test" in item["name"].lower() for item in results))

    def test_validation_error_nonexistent_field(self):
        """Test filtering with non-existent field returns empty results."""
        with pytest.raises(ValidationError):
            request = _make_authenticated_request(
                "GET", "/first_app/", query_params={"nonexistent": "value"}, token=self.token
            )
            _ = CRUDUtils.get(
                request=request,
                model_class=FirstApp,
                serializer_class=FirstAppSerializer,
            )

    def test_get_list_with_foreignkey_lookup(self):
        """Test filtering with ForeignKey lookup."""
        # Create SecondApp instances
        second_apps = [
            SecondApp.objects.create(name="second1", first_app=self.first_app_instances[0]),
            SecondApp.objects.create(name="second2", first_app=self.first_app_instances[1]),
        ]

        request = _make_authenticated_request(
            "GET", "/second_app/", query_params={"first_app__name": "test1"}, token=self.token
        )
        response = CRUDUtils.get(
            request=request,
            model_class=SecondApp,
            serializer_class=SecondAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["results"]
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "second1")


class TestCRUDUtilsPost(TestCase):
    """Test CRUDUtils.post() method."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username="testuser", password="testpass123")
        from rest_framework.authtoken.models import Token

        self.token = Token.objects.create(user=self.user)

    def test_post_create_instance(self):
        """Test creating a new instance."""
        request = _make_authenticated_request(
            "POST", "/first_app/", data={"name": "New Item", "description": "New Description"}, token=self.token
        )
        response = CRUDUtils.post(
            request=request,
            serializer_class=FirstAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Item")
        self.assertTrue(FirstApp.objects.filter(name="New Item").exists())

    def test_post_validation_error(self):
        """Test creating instance with validation error."""
        request = _make_authenticated_request(
            "POST", "/first_app/", data={"description": "Missing name"}, token=self.token
        )
        response = CRUDUtils.post(
            request=request,
            serializer_class=FirstAppSerializer,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)


class TestCRUDUtilsHelperMethods(TestCase):
    """Test helper methods."""

    def test_has_middle_wildcard(self):
        """Test detecting middle wildcard."""
        self.assertTrue(FilterUtils._has_middle_wildcard("t*t"))
        self.assertFalse(FilterUtils._has_middle_wildcard("test*"))
        self.assertFalse(FilterUtils._has_middle_wildcard("*test"))
        self.assertFalse(FilterUtils._has_middle_wildcard("*test*"))

    def test_wildcard_to_regex(self):
        """Test wildcard to regex conversion."""
        regex = FilterUtils._wildcard_to_regex("t*t")
        self.assertIn(".*", regex)
        self.assertTrue(regex.startswith("t"))
        self.assertTrue(regex.endswith("t"))
