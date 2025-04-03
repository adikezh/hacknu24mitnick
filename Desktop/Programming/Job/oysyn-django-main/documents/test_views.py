from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Document, Report, PlagiarismInstance

User = get_user_model()

class DocumentViewsTestCase(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='testuser@example.com', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.user.user_permissions.add(*Permission.objects.all())
        
        self.document = Document.objects.create(
            title='Test Document',
            document=SimpleUploadedFile("test.pdf", b"file_content"),
            created_by=self.user
        )
        
        self.report = Report.objects.create(
            title='Test Report',
            document=self.document,
            created_by=self.user,
            uniqueness=90,
            originality_percentage=85,
            plagiarism_percentage=5,
            citation_percentage=3,
            selfcitation_percentage=2
        )

    def test_home_page_view(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')

    def test_document_list_view(self):
        response = self.client.get(reverse('document_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'document_list.html')
        self.assertContains(response, self.document.title)

    def test_document_detail_view(self):
        response = self.client.get(reverse('document_detail', args=[self.document.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'document_detail.html')
        self.assertContains(response, self.document.title)
        self.assertNotContains(response, 'I should not be here.')

    def test_document_delete_view(self):
        response = self.client.post(reverse('document_delete', args=[self.document.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after successful deletion
        self.assertFalse(Document.objects.filter(id=self.document.id).exists())

    def test_document_create_view(self):
        data = {
            'title': 'New Test Document',
            'document': SimpleUploadedFile("new_test.pdf", b"new_file_content")
        }
        response = self.client.post(reverse('document_create'), data, follow=True)
        self.assertEqual(response.status_code, 200)  # Check if it's correctly handling the form
        self.assertTrue(Document.objects.filter(title='New Test Document').exists())

    def test_instance_update_view(self):
        instance = PlagiarismInstance.objects.create(
            report=self.report,
            title='Plagiarism Instance',
            module='Module',
            plagiarism_percentage=10
        )
        data = {'type': 'QUOTE'}
        response = self.client.post(reverse('instance_update', args=[instance.id]), data)
        self.assertEqual(response.status_code, 302)  # Redirect after successful update
        instance.refresh_from_db()
        self.assertEqual(instance.type, 'QUOTE')

    def test_report_list_view(self):
        response = self.client.get(reverse('report_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_list.html')
        self.assertNotContains(response, 'I should not be here.')

    def test_report_detail_view(self):
        response = self.client.get(reverse('report_details', args=[self.report.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_detail.html')
        self.assertContains(response, self.report.title)
        self.assertContains(response, self.document.title)

    def test_report_new_detail_view(self):
        response = self.client.get(reverse('report_new_details', args=[self.report.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'report_new_detail.html')
        self.assertContains(response, self.report.title)
        self.assertContains(response, self.document.title)
    
    def test_pdf_view(self):
        response = self.client.get(reverse('save_pdf') + f'?q={self.report.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertGreater(len(response.content), 0)

