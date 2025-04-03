import logging
import base64
from rest_framework import viewsets, generics, status, serializers, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.contrib.auth import login
from django.db.models import Q

from users.models import CustomUser
from organizations.models import Organization
from documents.models import Document, Report, PlagiarismInstance, Folder
from documents.tasks import process_document
from documents.text_processing import get_word_count
from documents.plagiarism_processing import recalculate_percentages
from documents.renderers import render_pdf_report, render_pdf_certificate

from .serializers import UserSerializer, OrganizationSerializer, DocumentSerializer, ReportSerializer, PlagiarismInstanceSerializer, FolderSerializer

logger = logging.getLogger(__name__)

# Custom Permissions
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit or delete it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD, or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the organization.
        return obj.created_by == request.user


# User Views
class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


class UserDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# Organization Views
class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_queryset(self):
        """
        This view should return a list of all the organizations
        for superusers, or only the organizations created by the current user.
        """
        user = self.request.user
        if user.is_superuser:
            return Organization.objects.all()
        return Organization.objects.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


# Document Views
class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Document.objects.all()
        elif user.is_moderator and user.organization:
            return Document.objects.filter(
                Q(created_by__organization=user.organization) |
                Q(created_by=user)
            )
        return Document.objects.filter(created_by=user)

    @swagger_auto_schema(
        request_body=DocumentSerializer,
        responses={201: DocumentSerializer}
    )
    def perform_create(self, serializer):
        user = self.request.user
        if user.organization and user.organization.checks_available <= 0:
            raise serializers.ValidationError("Not enough checks available. Please purchase more.")
        elif not user.organization and user.checks_available <= 0:
            raise serializers.ValidationError("Not enough checks available. Please purchase more.")

        document = serializer.save(created_by=user)
        with transaction.atomic():
            if user.organization:
                user.organization.checks_available -= 1
                user.organization.save()
            else:
                user.checks_available -= 1
                user.save()

            report = Report.objects.create(
                title=f"Report - {document.title}",
                document=document,
                created_by=user
            )

            document_id, report_id = document.id, report.id
            include_ocr = self.request.data.get('include_cr', False)
            ocr_languages = self.request.data.get('ocr_languages', ['rus'])
            ocr_languages_str = "+".join(ocr_languages)
            transaction.on_commit(lambda: process_document.apply_async(
                args=[document_id, report_id],
                kwargs={'include_ocr': include_ocr, 'ocr_languages': ocr_languages_str}
            ))

    def perform_update(self, serializer):
        document = serializer.save()
        report = document.reports.first()
        if report:
            word_count = get_word_count(document.document.path)
            instances = PlagiarismInstance.objects.filter(report=report)
            percentages = recalculate_percentages(word_count, instances)
            report.plagiarism_percentage, report.citation_percentage, report.selfcitation_percentage = percentages
            report.originality_percentage = report.calculate_final_originality()
            report.save()

    @action(detail=False, methods=['get'])
    def my_documents(self, request):
        documents = Document.objects.filter(created_by=request.user)
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def organization_documents(self, request):
        user = request.user
        if not user.organization:
            return Response(
                {"detail": "You are not part of any organization."},
                status=status.HTTP_403_FORBIDDEN
            )
        documents = Document.objects.filter(created_by__organization=user.organization)
        page = self.paginate_queryset(documents)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(documents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def recheck(self, request, pk=None):
        document = self.get_object()
        report = document.reports.first()
        if not report:
            return Response(
                {"detail": "No report found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        user = request.user
        if user.organization and user.organization.checks_available <= 0:
            return Response(
                {"detail": "Not enough checks available. Please purchase more."},
                status=status.HTTP_403_FORBIDDEN
            )
        elif not user.organization and user.checks_available <= 0:
            return Response(
                {"detail": "Not enough checks available. Please purchase more."},
                status=status.HTTP_403_FORBIDDEN
            )

        with transaction.atomic():
            if user.organization:
                user.organization.checks_available -= 1
                user.organization.save()
            else:
                user.checks_available -= 1
                user.save()

            include_ocr = request.data.get('include_cr', False)
            ocr_languages = request.data.get('ocr_languages', ['rus'])
            ocr_languages_str = "+".join(ocr_languages)
            transaction.on_commit(lambda: process_document.apply_async(
                args=[document.id, report.id],
                kwargs={'include_ocr': include_ocr, 'ocr_languages': ocr_languages_str}
            ))

        return Response({"detail": "Document recheck initiated."})

    @action(detail=True, methods=['get'])
    def generate_report(self, request, pk=None):
        document = self.get_object()
        report = document.reports.first()
        if not report:
            return Response(
                {"detail": "No report found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            pdf = render_pdf_report('report_template.html', {'report': report, 'report_id': report.id})
            if pdf is None:
                return Response({"detail": "Error generating PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            response = JsonResponse({'pdf': base64.b64encode(pdf).decode('utf-8')})
            return response
        except Exception as e:
            logger.error(f"Error generating report: {e}")
            return Response({"detail": "Error generating report"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def generate_certificate(self, request, pk=None):
        document = self.get_object()
        report = document.reports.first()
        if not report:
            return Response(
                {"detail": "No report found for this document."},
                status=status.HTTP_404_NOT_FOUND
            )
        try:
            pdf = render_pdf_certificate('certificate_template.html', {'report': report, 'report_id': report.id})
            if pdf is None:
                return Response({"detail": "Error generating PDF"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            response = JsonResponse({'pdf': base64.b64encode(pdf).decode('utf-8')})
            return response
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            return Response({"detail": "Error generating certificate"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Report Views
class ReportViewSet(viewsets.ModelViewSet):
    queryset = Report.objects.all()
    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]


# Plagiarism Instance Views
class PlagiarismInstanceViewSet(viewsets.ModelViewSet):
    queryset = PlagiarismInstance.objects.all()
    serializer_class = PlagiarismInstanceSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        instance = serializer.save()
        report = instance.report
        word_count = get_word_count(report.document.document.path)
        instances = PlagiarismInstance.objects.filter(report=report)
        percentages = recalculate_percentages(word_count, instances)
        report.plagiarism_percentage, report.citation_percentage, report.selfcitation_percentage = percentages
        report.originality_percentage = report.calculate_final_originality()
        report.save()


# Folder Views
class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return Folder.objects.all()
        return Folder.objects.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        folder = self.get_object()
        new_parent_id = request.data.get('new_parent_id')
        new_parent = get_object_or_404(Folder, id=new_parent_id)
        folder.parent_folder = new_parent
        folder.save()
        return Response({"detail": "Folder moved successfully."})

    @action(detail=True, methods=['post'])
    def delete(self, request, pk=None):
        folder = self.get_object()
        folder.delete()
        return Response({"detail": "Folder deleted successfully."})


# Additional Views
class ImpersonateUserView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_PATH, description="ID of the user to impersonate", type=openapi.TYPE_INTEGER)
        ],
        responses={200: 'Success', 403: 'Forbidden', 404: 'Not Found'}
    )
    def post(self, request, user_id):
        target_user = get_object_or_404(CustomUser, id=user_id)
        if request.user.is_superuser:
            pass
        elif request.user.is_moderator:
            if target_user.organization != request.user.organization:
                return Response({"detail": "You cannot impersonate users from another organization."}, status=status.HTTP_403_FORBIDDEN)
        else:
            return Response({"detail": "You do not have permission to impersonate users."}, status=status.HTTP_403_FORBIDDEN)

        if "original_user_id" not in request.session:
            request.session["original_user_id"] = request.user.id

        backend = request.session.get('_auth_user_backend', 'django.contrib.auth.backends.ModelBackend')
        target_user.backend = backend
        login(request, target_user, backend=backend)
        return Response({"detail": f"You are now impersonating {target_user.email}."})


class StopImpersonationView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: 'Success', 400: 'Bad Request', 404: 'Not Found'}
    )
    def post(self, request):
        original_user_id = request.session.pop('original_user_id', None)
        if not original_user_id:
            return Response({"detail": "You are not impersonating any user."}, status=status.HTTP_400_BAD_REQUEST)

        original_user = get_object_or_404(CustomUser, id=original_user_id)
        backend = request.session.get('_auth_user_backend', 'django.contrib.auth.backends.ModelBackend')
        original_user.backend = backend
        login(request, original_user, backend=backend)
        return Response({"detail": f"You have returned to your account {original_user.email}."})
