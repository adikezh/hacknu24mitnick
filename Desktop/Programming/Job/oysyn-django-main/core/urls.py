from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.utils.translation import gettext_lazy as _
from django.conf.urls.i18n import i18n_patterns

urlpatterns = i18n_patterns(
    path('noaccess/', admin.site.urls),
    path('rosetta/', include('rosetta.urls')),
    path('accounts/', include('allauth.urls')),
    path('', include('documents.urls')),
    path('', include('users.urls')),
    path('organization/', include('organizations.urls')),
    path('news/', include('news.urls')),
    path('comments/', include('comments.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('payments/', include('payments.urls')),
    path('api/', include('api.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
