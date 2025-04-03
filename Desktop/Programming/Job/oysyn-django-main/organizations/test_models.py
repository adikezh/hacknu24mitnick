from django.db import DataError
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Organization

User = get_user_model()

class OrganizationModelTestCase(TestCase):
    def setUp(self):
        # Create a user instance to associate with the organization
        self.user = User.objects.create_user(username='testuser', password='testpassword')
    
    def test_create_organization(self):
        # Create an Organization instance
        organization = Organization.objects.create(
            created_by=self.user,
            title='Test Organization',
            city='ALA',
            address='123 Test St',
            description='A test organization'
        )
        
        # Verify that the instance was created successfully
        self.assertEqual(Organization.objects.count(), 1)
        self.assertEqual(organization.title, 'Test Organization')
        self.assertEqual(organization.city, 'ALA')
        self.assertEqual(organization.address, '123 Test St')
        self.assertEqual(organization.description, 'A test organization')
        self.assertEqual(organization.created_by, self.user)
    
    def test_organization_string_representation(self):
        organization = Organization.objects.create(
            created_by=self.user,
            title='Test Organization',
            city='ALA',
            address='123 Test St'
        )
        
        # Verify that the string representation matches the title
        self.assertEqual(str(organization), 'Test Organization')
    
    def test_city_choices(self):
        # Verify that the city choices are as expected
        valid_cities = dict(Organization.CITY_CHOICES)
        self.assertIn('ALA', valid_cities)
        self.assertIn('NQZ', valid_cities)
        self.assertIn('KGF', valid_cities)
        self.assertIn('CIT', valid_cities)
        self.assertIn('AKX', valid_cities)
        self.assertIn('PWQ', valid_cities)
        self.assertIn('UKK', valid_cities)
    
    
    def test_address_field_max_length(self):
        # Test that the address field enforces the maximum length constraint
        long_address = 'A' * 301  # 301 characters long
        with self.assertRaises(DataError):
            Organization.objects.create(
                created_by=self.user,
                title='Test Organization',
                city='ALA',
                address=long_address
            )
    
    def test_description_field_blank(self):
        # Test that the description field can be left blank
        organization = Organization.objects.create(
            created_by=self.user,
            title='Test Organization',
            city='ALA',
            address='123 Test St'
        )
        
        # Verify that the description can be empty
        self.assertEqual(organization.description, '')
