"""
Comprehensive tests for Department views and models.

# all tests
cd django_basic_app
uv run python manage.py test apps.department.tests

# specific test case
uv run python manage.py test apps.department.tests.TestDepartmentAPI.test_list_all_instances
"""

from apps.employee.models import Employee
from django.contrib.auth import get_user_model
from django.test import TestCase
from django_versioned_models.models import Release
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Department

User = get_user_model()


def _release() -> Release:
    """Create a test release (unlocked) for versioned models."""
    release, _ = Release.objects.get_or_create(
        version="test-release",
        defaults={"description": "Test release", "is_locked": False},
    )
    return release


class TestDepartmentModel(TestCase):
    """Test Department model."""

    def setUp(self) -> None:
        self.release = _release()

    def test_model_str(self) -> None:
        """Test model __str__ method."""
        instance = Department.objects.create(name="Test Model", release=self.release)
        self.assertEqual(str(instance), "Test Model")

    def test_model_foreignkey_relationship(self) -> None:
        """Test ForeignKey relationship."""
        employee = Employee.objects.create(name="test1", release=self.release)
        department = Department.objects.create(name="Test", employee=employee, release=self.release)

        self.assertEqual(department.employee, employee)
        self.assertEqual(department.employee.name, "test1")


class TestDepartmentAPI(TestCase):
    """Test Department API endpoints."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.release = _release()
        self.user = User.objects.create_user(username="testuser", password="testpass123")

        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.employee = Employee.objects.create(name="test1", description="Test 1", release=self.release)

    def test_list_all_instances(self) -> None:
        """Test listing all Department instances."""
        Department.objects.create(name="dept1", employee=self.employee, release=self.release)
        Department.objects.create(name="dept2", employee=None, release=self.release)

        response = self.api_client.get("/department/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 2)

    def test_create_instance(self) -> None:
        """Test creating a new Department instance."""
        data = {
            "name": "New Dept",
            "description": "New Description",
            "employee_name": self.employee.name,
            "release": self.release.pk,
        }
        response = self.api_client.post("/department/", data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "New Dept")
        self.assertTrue(Department.objects.filter(name="New Dept").exists())

    def test_filter_with_foreignkey(self) -> None:
        """Test filtering with ForeignKey lookup."""
        Department.objects.create(name="dept1", employee=self.employee, release=self.release)
        Department.objects.create(name="dept2", employee=None, release=self.release)

        response = self.api_client.get("/department/?employee__name=test1")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["name"], "dept1")

    def test_requires_authentication(self) -> None:
        """Test that endpoints require authentication."""
        client = APIClient()
        response = client.get("/department/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
