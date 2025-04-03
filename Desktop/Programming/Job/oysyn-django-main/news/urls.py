from django.urls import path
from .views import NewsListView, NewsDetailView, NewsCreateView, NewsUpdateView, NewsDeleteView

app_name = 'news'

urlpatterns = [
    # path('list/', NewsListView.as_view(), name='list'),
    # path('<slug:slug>/', NewsDetailView.as_view(), name='detail'),
    # path('create/', NewsCreateView.as_view(), name='create'),
    # path('<slug:slug>/edit/', NewsUpdateView.as_view(), name='update'),
    # path('<slug:slug>/delete/', NewsDeleteView.as_view(), name='delete'),
]
