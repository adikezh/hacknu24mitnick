from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.contrib.auth.forms import UserChangeForm

User = get_user_model()

class UserViewsTests(TestCase):
    
    def setUp(self):
        """Create a user and client for testing."""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.client.login(username='testuser', password='testpassword')

    def test_user_detail_view(self):
        """Test the user detail view."""
        response = self.client.get(reverse('user_detail'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_detail.html')
        self.assertContains(response, self.user.username)
        self.assertContains(response, self.user.email)

    def test_user_update_view_get(self):
        """Test the user update view GET request."""
        response = self.client.get(reverse('user_update'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'user_update.html')
        self.assertIsInstance(response.context['form'], UserChangeForm)

    def test_user_update_view_post_valid(self):
        """Test the user update view POST request with valid data."""
        response = self.client.post(reverse('user_update'), {
            'email': 'updateduser@example.com',
            'first_name': 'Updated',
            'last_name': 'User'
        })
        
        # Ensure the view redirects after a successful form submission
        self.assertEqual(response.status_code, 302)  # Should redirect to success_url

        # Refresh the user instance from the database
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'updateduser@example.com')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')


    def test_user_update_view_post_invalid(self):
        """Test the user update view POST request with invalid data."""
        response = self.client.post(reverse('user_update'), {
            'email': 'invalidemail',  # Invalid email
        })
        self.assertEqual(response.status_code, 200)  # Should stay on the same page

        # Check that the form instance is available in the response context
        form = response.context.get('form')
        self.assertIsInstance(form, UserChangeForm)
        
        # Ensure the form is not valid
        self.assertFalse(form.is_valid())

        # Assert specific form errors
        self.assertIn('email', form.errors)
        self.assertEqual(form.errors['email'], ['Enter a valid email address.'])
        