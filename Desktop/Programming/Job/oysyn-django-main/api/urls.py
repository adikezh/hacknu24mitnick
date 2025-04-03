from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .views import UserViewSet, OrganizationViewSet, DocumentViewSet, ReportViewSet, PlagiarismInstanceViewSet, FolderViewSet, UserDetailView, ImpersonateUserView, StopImpersonationView

# Initialize the router
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'organizations', OrganizationViewSet)
router.register(r'documents', DocumentViewSet)
router.register(r'reports', ReportViewSet)
router.register(r'plagiarism-instances', PlagiarismInstanceViewSet)
router.register(r'folders', FolderViewSet)

# Define the schema view for Swagger documentation
schema_view = get_schema_view(
    openapi.Info(
        title="OySyn API - The best plagiarism detection service",
        default_version='v1',
        description="API documentation for OySyn API",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="support@globalaeon.tech"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(AllowAny,),
)

# Define the token authentication URLs
token_auth_patterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

# Combine the router URLs and token auth URLs
urlpatterns = router.urls + token_auth_patterns

# Add Swagger and ReDoc URLs
urlpatterns += [
    re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('impersonate/<int:user_id>/', ImpersonateUserView.as_view(), name='impersonate-user'),
    path('stop-impersonation/', StopImpersonationView.as_view(), name='stop-impersonation'),
]
