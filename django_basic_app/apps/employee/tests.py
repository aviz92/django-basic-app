"""
Comprehensive tests for Employee views and models.

# all tests
cd django_basic_app
uv run python manage.py test apps.employee.tests

# specific test case
uv run python manage.py test apps.employee.tests.TestEmployeeAPI.test_list_all_instances
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django_versioned_models.models import Release
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Employee

User = get_user_model()


def _release() -> Release:
    """Create a test release (unlocked) for versioned models."""
    release, _ = Release.objects.get_or_create(
        version="test-release",
        defaults={"description": "Test release", "is_locked": False},
    )
    return release


class TestEmployeeModel(TestCase):
    """Test Employee model."""

    def setUp(self) -> None:
        self.release = _release()

    def test_model_str(self) -> None:
        """Test model __str__ method."""
        instance = Employee.objects.create(name="Test Model", release=self.release)
        self.assertEqual(str(instance), "Test Model")

    def test_model_created_at_auto(self) -> None:
        """Test that created_at is auto-set."""
        instance = Employee.objects.create(name="Test", release=self.release)
        self.assertIsNotNone(instance.created_at)


class TestEmployeeAPI(TestCase):
    """Test Employee API endpoints."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.release = _release()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_list_all_instances(self) -> None:
        """Test listing all Employee instances."""
        Employee.objects.create(name="test1", description="Description 1", release=self.release)
        Employee.objects.create(name="test2", description="Description 2", release=self.release)

        response = self.api_client.get("/employee/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_create_instance(self) -> None:
        """Test creating a new Employee instance."""
        data = {
            "name": "New Item",
            "description": "New Description",
            "release": self.release.pk,
        }
        response = self.api_client.post("/employee/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Item")
        self.assertTrue(Employee.objects.filter(name="New Item").exists())

    def test_retrieve_instance(self) -> None:
        """Test retrieving a single instance."""
        instance = Employee.objects.create(name="test1", description="Test", release=self.release)
        response = self.api_client.get(f"/employee/{instance.pk}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], instance.pk)
        self.assertEqual(response.data["name"], "test1")

    def test_filter_with_wildcard(self) -> None:
        """Test filtering with wildcard."""
        Employee.objects.create(name="test1", description="Test 1", release=self.release)
        Employee.objects.create(name="test2", description="Test 2", release=self.release)
        Employee.objects.create(name="other", description="Other", release=self.release)

        response = self.api_client.get("/employee/?name=test*")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_update_instance(self) -> None:
        """Test updating an instance."""
        instance = Employee.objects.create(name="Original", description="Original", release=self.release)
        data = {
            "name": "Updated",
            "description": "Updated",
            "release": self.release.pk,
        }
        response = self.api_client.put(f"/employee/{instance.pk}/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance.refresh_from_db()
        self.assertEqual(instance.name, "Updated")

    def test_delete_instance(self) -> None:
        """Test deleting an instance."""
        instance = Employee.objects.create(name="To Delete", release=self.release)
        pk = instance.pk
        response = self.api_client.delete(f"/employee/{pk}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Employee.objects.filter(pk=pk).exists())

    def test_requires_authentication(self) -> None:
        """Test that endpoints require authentication."""
        client = APIClient()  # No authentication
        response = client.get("/employee/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
