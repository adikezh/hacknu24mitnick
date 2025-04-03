from django.urls import path
from . import views
from .views import generate_report_view, generate_certificate_view, generate_new_certificate_view, generate_new_report_view

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('document/create/', views.DocumentCreateView.as_view(), name='document_create'),
    path('document/list/', views.DocumentListView.as_view(), name='document_list'),
    path('document/<pk>/', views.DocumentDetailView.as_view(), name='document_detail'),
    path('document/<pk>/delete/', views.DocumentDeleteView.as_view(), name='document_delete'),
    path('document/<pk>/update/', views.DocumentUpdateView.as_view(), name='document_update'),
    path('updateinstancetype/<int:pk>/', views.DocumentHighlightView.as_view(), name='document_highlight'),
    path('documents/move/', views.MoveDocumentsView.as_view(), name='move_documents'),
    path('documents/delete/', views.DeleteDocumentsView.as_view(), name='delete_documents'),
    path('documents/search/', views.DocumentSearchPageView.as_view(), name='document_search_page'),
    path('documents/search/api/', views.DocumentSearchView.as_view(), name='document_search_api'),
    path('report/list/', views.ReportListView.as_view(), name='report_list'),
    path('report/detail/<pk>/', views.ReportDetailView.as_view(), name='report_details'),
    path('report/new_detail/<pk>/', views.ReportNewDetailView.as_view(), name='report_new_details'),
    path('instance/update/<pk>/', views.InstanceUpdateView.as_view(), name='instance_update'),
    path('pdf_report/', generate_report_view, name='generate_report'),
    path('pdf_certificate/', generate_certificate_view, name='generate_certificate'),

    path('pdf_certificate_new/', generate_new_certificate_view, name='generate_certificate_new'),
    path('pdf_report_new/', generate_new_report_view, name='generate_report_new'),

    path('save_pdf/', generate_report_view, name='save_pdf'),
    path('folders/', views.FolderListView.as_view(), name='folder_list'),
    path('folders/create/', views.FolderCreateAjaxView.as_view(), name='folder_create_ajax'),
    path('folders/<int:folder_id>/update/', views.FolderUpdateAjaxView.as_view(), name='folder_update_ajax'),
    path('folders/<int:folder_id>/move/', views.FolderMoveAjaxView.as_view(), name='folder_move_ajax'),
    path('folders/<int:pk>/delete/', views.FolderDeleteAjaxView.as_view(), name='folder_delete_ajax'),
    path('folders/<int:folder_id>/documents/', views.DocumentListView.as_view(), name='document_list_root'),
    path('about-oysyn/', views.AboutOysynView.as_view(), name='about_oysyn'),
]
