from django.urls import reverse
from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Organization

User = get_user_model()

class OrganizationViewsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.other_user = User.objects.create_user(username='otheruser', password='otherpassword')
        self.organization = Organization.objects.create(
            created_by=self.user,
            title='Test Organization',
            city='ALA',
            address='123 Test St',
            description='A test organization'
        )

    def test_organization_list_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('organization_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'organizations/organization_list.html')
        self.assertContains(response, 'Test Organization')

    def test_organization_detail_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('organization_detail', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'organizations/organization_detail.html')
        self.assertContains(response, 'Test Organization')

    def test_organization_create_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('organization_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'organizations/organization_form.html')
        
        response = self.client.post(reverse('organization_create'), {
            'title': 'New Organization',
            'city': 'NQZ',
            'address': '456 New St',
            'description': 'A new test organization',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('organization_list'))
        self.assertTrue(Organization.objects.filter(title='New Organization').exists())

    def test_organization_update_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('organization_update', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'organizations/organization_form.html')
        
        response = self.client.post(reverse('organization_update', args=[self.organization.pk]), {
            'title': 'Updated Organization',
            'city': 'CIT',
            'address': '789 Updated St',
            'description': 'An updated test organization',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('organization_list'))
        self.organization.refresh_from_db()
        self.assertEqual(self.organization.title, 'Updated Organization')

    def test_organization_delete_view(self):
        self.client.login(username='testuser', password='testpassword')
        response = self.client.get(reverse('organization_delete', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'organizations/organization_confirm_delete.html')
        
        response = self.client.post(reverse('organization_delete', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('organization_list'))
        self.assertFalse(Organization.objects.filter(pk=self.organization.pk).exists())

    def test_access_restriction_for_unauthorized_users(self):
        self.client.login(username='otheruser', password='otherpassword')
        response = self.client.get(reverse('organization_detail', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('organization_update', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse('organization_delete', args=[self.organization.pk]))
        self.assertEqual(response.status_code, 403)
