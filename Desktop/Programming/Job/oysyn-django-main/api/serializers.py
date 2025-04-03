from rest_framework import serializers
from users.models import CustomUser
from organizations.models import Organization
from documents.models import Document, Report, PlagiarismInstance, Folder

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']

class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ['id', 'title', 'city', 'address', 'description', 'created_by']

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'title', 'document', 'created_by', 'created_at', 'status', 'include_ocr', 'ocr_languages']

class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['id', 'title', 'document', 'created_by', 'created_at', 'originality_percentage', 'plagiarism_percentage', 'citation_percentage', 'selfcitation_percentage']

class PlagiarismInstanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlagiarismInstance
        fields = ['id', 'report', 'url', 'indices', 'type', 'title', 'module', 'plagiarism_percentage']

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'parent_folder', 'created_by', 'created_at']
