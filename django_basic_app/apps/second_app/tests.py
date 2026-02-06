"""
Comprehensive tests for SecondApp views and models.

# all tests
cd django_basic_app
uv run python manage.py test apps.second_app.tests

# specific app tests
uv run python manage.py test apps.second_app.tests

# specific test case
uv run python manage.py test apps.second_app.tests.TestSecondAppAPI.test_list_all_instances
"""

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from apps.first_app.models import FirstApp
from .models import SecondApp

User = get_user_model()


class TestSecondAppModel(TestCase):
    """Test SecondApp model."""

    def test_model_str(self):
        """Test model __str__ method."""
        instance = SecondApp.objects.create(name='Test Model')
        self.assertEqual(str(instance), 'Test Model')

    def test_model_foreignkey_relationship(self):
        """Test ForeignKey relationship."""
        first_app = FirstApp.objects.create(name='test1')
        second_app = SecondApp.objects.create(name='Test', first_app=first_app)

        self.assertEqual(second_app.first_app, first_app)
        self.assertEqual(second_app.first_app.name, 'test1')


class TestSecondAppAPI(TestCase):
    """Test SecondApp API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        from rest_framework.authtoken.models import Token
        self.token = Token.objects.create(user=self.user)
        self.api_client = APIClient()
        self.api_client.credentials(HTTP_AUTHORIZATION=f'Token {self.token.key}')

        # Create FirstApp for ForeignKey
        self.first_app = FirstApp.objects.create(name='test1', description='Test 1')

    def test_list_all_instances(self):
        """Test listing all SecondApp instances."""
        SecondApp.objects.create(name='second1', first_app=self.first_app)
        SecondApp.objects.create(name='second2', first_app=None)

        response = self.api_client.get('/second_app/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(response.data['count'], 2)

    def test_create_instance(self):
        """Test creating a new SecondApp instance."""
        data = {
            'name': 'New Second',
            'description': 'New Description',
            'first_app': self.first_app.name
        }
        response = self.api_client.post('/second_app/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Second')
        self.assertTrue(SecondApp.objects.filter(name='New Second').exists())

    def test_filter_with_foreignkey(self):
        """Test filtering with ForeignKey lookup."""
        SecondApp.objects.create(name='second1', first_app=self.first_app)
        SecondApp.objects.create(name='second2', first_app=None)

        response = self.api_client.get('/second_app/?first_app__name=test1')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'second1')

    def test_requires_authentication(self):
        """Test that endpoints require authentication."""
        client = APIClient()  # No authentication
        response = client.get('/second_app/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
