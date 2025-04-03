from django.urls import path
from .views import CommentCreateView, CommentDeleteView

app_name = 'comments'

urlpatterns = [
    path('comments/create/', CommentCreateView.as_view(), name='create'),
    path('comments/delete/<int:comment_id>/', CommentDeleteView.as_view(), name='delete'),
]
