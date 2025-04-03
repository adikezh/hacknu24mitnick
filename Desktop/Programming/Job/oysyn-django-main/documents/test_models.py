from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Document, Report, PlagiarismInstance
from datetime import datetime
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class DocumentModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.document = Document.objects.create(
            title='Test Document',
            document=SimpleUploadedFile("test.pdf", b"file_content"),
            created_by=self.user
        )

    def test_document_creation(self):
        self.assertTrue(isinstance(self.document, Document))
        self.assertEqual(str(self.document), self.document.title)

    def test_is_checked(self):
        self.assertFalse(self.document.is_checked())
        self.document.status = Document.CHECKED
        self.document.save()
        self.assertTrue(self.document.is_checked())


class ReportModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
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
            human_written_percentage=80,
            chatgpt_generated_percentage=10,
            originality_percentage=85,
            plagiarism_percentage=5,
            citation_percentage=3,
            selfcitation_percentage=2,
            shingles_total_number=100
        )

    def test_report_creation(self):
        self.assertTrue(isinstance(self.report, Report))
        self.assertEqual(str(self.report), self.report.title)

    def test_calculate_final_originality(self):
        self.assertEqual(self.report.calculate_final_originality(), 90)


class PlagiarismInstanceModelTests(TestCase):
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        self.document = Document.objects.create(
            title='Test Document',
            document=SimpleUploadedFile("test.pdf", b"file_content"),
            created_by=self.user
        )
        self.report = Report.objects.create(
            title='Test Report',
            document=self.document,
            created_by=self.user
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

    def test_plagiarism_instance_creation(self):
        self.assertTrue(isinstance(self.plagiarism_instance, PlagiarismInstance))
        self.assertEqual(str(self.plagiarism_instance), self.plagiarism_instance.title)

    def test_plagiarism_instance_default_title(self):
        self.plagiarism_instance.title = ''
        self.plagiarism_instance.save()
        self.assertEqual(str(self.plagiarism_instance), f"Plagiarism instance {self.plagiarism_instance.id}")
