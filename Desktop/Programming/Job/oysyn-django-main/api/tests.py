import base64
import logging
import qrcode

from io import BytesIO
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from users.models import CustomUser
from unittest.mock import patch, Mock
from organizations.models import Organization
from documents.models import Document, Report, PlagiarismInstance, Folder
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)


class APITests(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        # Generate test QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data('https://test.com/test-qr')
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        
        # Save QR code properly
        qr_image_io = BytesIO()
        img.save(qr_image_io, format='PNG')
        qr_image_io.seek(0)
        self.test_qr_data = qr_image_io.getvalue()
        self.test_qr_base64 = base64.b64encode(self.test_qr_data).decode('utf-8')
        
        self.client.login(username='testuser', password='testpassword')
        self.organization = Organization.objects.create(
            title='Test Organization',
            created_by=self.user,
            city='ALA',
            address='123 Test St'
        )
        self.document = Document.objects.create(
            title='Test Document',
            author='Test Author',
            document=ContentFile(b"test content", name='test.pdf'),
            created_by=self.user
        )
        self.report = Report.objects.create(
            title='Test Report',
            document=self.document,
            created_by=self.user,
            citation_percentage=10,
            selfcitation_percentage=5,
            chatgpt_generated_percentage=15
        )
        self.plagiarism_instance = PlagiarismInstance.objects.create(
            report=self.report,
            url='http://example.com',
            indices=[0, 10],
            type=PlagiarismInstance.PLAGIARISM,
            title='Example Title',
            module='Example Module',
            plagiarism_percentage=20
        )
        self.folder = Folder.objects.create(
            name='Test Folder',
            created_by=self.user
        )

    def authenticate(self):
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {'username': 'testuser', 'password': 'testpassword'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + response.data['access'])

    def test_create_user(self):
        self.authenticate()
        url = reverse('user-list')
        data = {'username': 'newuser', 'email': 'newuser@example.com', 'password': 'newpassword'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_user(self):
        self.authenticate()
        url = reverse('user-detail')
        data = {'username': 'updateduser', 'email': 'updateduser@example.com'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_organization(self):
        self.authenticate()
        url = reverse('organization-list')
        data = {'title': 'New Organization', 'created_by': self.user.id, 'city': 'ALA', 'address': '456 New St'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_organization(self):
        self.authenticate()
        url = reverse('organization-detail', args=[self.organization.id])
        data = {'title': 'Updated Organization', 'created_by': self.user.id, 'city': 'ALA', 'address': '789 Updated St'}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_document(self):
        self.authenticate()
        url = reverse('document-list')
        data = {'title': 'New Document', 'document': SimpleUploadedFile("new.pdf", b"file_content"), 'created_by': self.user.id}
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_document(self):
        self.authenticate()
        url = reverse('document-detail', args=[self.document.id])
        data = {'title': 'Updated Document', 'document': SimpleUploadedFile("updated.pdf", b"updated_file_content"), 'created_by': self.user.id}
        response = self.client.put(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_recheck_document(self):
        self.authenticate()
        url = reverse('document-recheck', args=[self.document.id])
        data = {'include_cr': False, 'ocr_languages': ['rus']}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_report(self):
        self.authenticate()
        url = reverse('report-list')
        data = {'title': 'New Report', 'document': self.document.id, 'created_by': self.user.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_report(self):
        self.authenticate()
        url = reverse('report-detail', args=[self.report.id])
        data = {'title': 'Updated Report', 'document': self.document.id, 'created_by': self.user.id}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_plagiarism_instance(self):
        self.authenticate()
        url = reverse('plagiarisminstance-list')
        data = {'report': self.report.id, 'url': 'http://newexample.com', 'indices': [0, 20], 'type': PlagiarismInstance.PLAGIARISM, 'title': 'New Title', 'module': 'New Module', 'plagiarism_percentage': 30}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_plagiarism_instance(self):
        self.authenticate()
        url = reverse('plagiarisminstance-detail', args=[self.plagiarism_instance.id])
        data = {'title': 'Updated Title', 'report': self.report.id, 'url': 'http://newexample.com', 'indices': [0, 20], 'type': PlagiarismInstance.PLAGIARISM, 'module': 'New Module', 'plagiarism_percentage': 30}
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_folder(self):
        self.authenticate()
        url = reverse('folder-list')
        data = {
            'name': 'New Folder',
            'created_by': self.user.id,
            'parent_folder': None,  # Add required parent_folder field
            'description': 'Test folder description'  # Add optional description
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Folder.objects.count(), 2)  # Including the one created in setUp
        self.assertEqual(Folder.objects.latest('id').name, 'New Folder')

    def test_update_folder(self):
        self.authenticate()
        url = reverse('folder-detail', args=[self.folder.id])
        data = {
            'name': 'Updated Folder',
            'created_by': self.user.id,
            'parent_folder': None,
            'description': 'Updated folder description'
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.folder.refresh_from_db()
        self.assertEqual(self.folder.name, 'Updated Folder')

    def test_move_folder(self):
        self.authenticate()
        new_parent = Folder.objects.create(name='New Parent Folder', created_by=self.user)
        url = reverse('folder-move', args=[self.folder.id])
        data = {'new_parent_id': new_parent.id}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_folder(self):
        self.authenticate()
        url = reverse('folder-delete', args=[self.folder.id])
        response = self.client.post(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
