"""
Comprehensive tests for FirstApp views and models.

# all tests
cd django_basic_app
uv run python manage.py test apps.first_app.tests

# specific app tests
uv run python manage.py test apps.first_app.tests

# specific test case
uv run python manage.py test apps.first_app.tests.TestFirstAppAPI.test_list_all_instances
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import FirstApp

User = get_user_model()


class TestFirstAppModel(TestCase):
    """Test FirstApp model."""

    def test_model_str(self):
        """Test model __str__ method."""
        instance = FirstApp.objects.create(name='Test Model')
        self.assertEqual(str(instance), 'Test Model')

    def test_model_created_at_auto(self):
        """Test that created_at is auto-set."""
        instance = FirstApp.objects.create(name='Test')
        self.assertIsNotNone(instance.created_at)


class TestFirstAppAPI(TestCase):
    """Test FirstApp API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

    def test_list_all_instances(self):
        """Test listing all FirstApp instances."""
        FirstApp.objects.create(name='test1', description='Description 1')
        FirstApp.objects.create(name='test2', description='Description 2')

        response = self.api_client.get('/first_app/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_create_instance(self):
        """Test creating a new FirstApp instance."""
        data = {'name': 'New Item', 'description': 'New Description'}
        response = self.api_client.post('/first_app/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Item')
        self.assertTrue(FirstApp.objects.filter(name='New Item').exists())

    def test_retrieve_instance(self):
        """Test retrieving a single instance."""
        instance = FirstApp.objects.create(name='test1', description='Test')
        response = self.api_client.get(f'/first_app/{instance.pk}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], instance.pk)
        self.assertEqual(response.data['name'], 'test1')

    def test_filter_with_wildcard(self):
        """Test filtering with wildcard."""
        FirstApp.objects.create(name='test1', description='Test 1')
        FirstApp.objects.create(name='test2', description='Test 2')
        FirstApp.objects.create(name='other', description='Other')

        response = self.api_client.get('/first_app/?name=test*')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_update_instance(self):
        """Test updating an instance."""
        instance = FirstApp.objects.create(name='Original', description='Original')
        data = {'name': 'Updated', 'description': 'Updated'}
        response = self.api_client.put(f'/first_app/{instance.pk}/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        instance.refresh_from_db()
        self.assertEqual(instance.name, 'Updated')

    def test_delete_instance(self):
        """Test deleting an instance."""
        instance = FirstApp.objects.create(name='To Delete')
        pk = instance.pk
        response = self.api_client.delete(f'/first_app/{pk}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(FirstApp.objects.filter(pk=pk).exists())

    def test_requires_authentication(self):
        """Test that endpoints require authentication."""
        client = APIClient()  # No authentication
        response = client.get('/first_app/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
