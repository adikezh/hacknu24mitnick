from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomUserModelTests(TestCase):

    def test_create_user_with_role(self):
        """Test creating a user with a specific role."""
        user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword',
            role=User.Role.MODERATOR
        )
        self.assertEqual(user.role, User.Role.MODERATOR)
    
    def test_create_user_with_default_role(self):
        """Test creating a user without specifying a role defaults to 'EXPERT'."""
        user = User.objects.create_user(
            username='defaultuser',
            email='defaultuser@example.com',
            password='defaultpassword'
        )
        self.assertEqual(user.role, User.Role.EXPERT)
    
    def test_invalid_role(self):
        """Test invalid role raises a validation error."""
        with self.assertRaises(ValidationError):
            user = User(
                username='invalidroleuser',
                email='invalidroleuser@example.com',
                password='invalidpassword',
                role='INVALID_ROLE'
            )
            user.full_clean()  # This will trigger the validation

    def test_role_choices(self):
        """Test role choices are as expected."""
        # Define valid roles as codes
        valid_roles = [User.Role.MODERATOR, User.Role.EXPERT]
        
        # Extract role codes from choices
        role_codes = [choice[0] for choice in User.Role.choices]
        
        # Ensure that valid roles are in role codes
        for role in valid_roles:
            self.assertIn(role, role_codes)
        
        # Ensure that an invalid role is not in role codes
        invalid_role = 'INVALID_ROLE'
        self.assertNotIn(invalid_role, role_codes)
    
    def test_user_creation_with_custom_role(self):
        """Test creating a user with a custom role."""
        for role in User.Role.choices:
            user = User.objects.create_user(
                username=f'{role[0]}_user',
                email=f'{role[0]}_user@example.com',
                password='testpassword',
                role=role[0]  # Use the role code
            )
            self.assertEqual(user.role, role[0])
