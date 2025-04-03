from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import News
from .forms import NewsForm


class NewsListView(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'

class NewsDetailView(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'

class NewsCreateView(CreateView):
    model = News
    template_name = 'news/news_form.html'
    form_class = NewsForm
    success_url = reverse_lazy('news:list')

class NewsUpdateView(UpdateView):
    model = News
    template_name = 'news/news_form.html'
    form_class = NewsForm
    success_url = reverse_lazy('news:list')

class NewsDeleteView(DeleteView):
    model = News
    template_name = 'news/news_confirm_delete.html'
    success_url = reverse_lazy('news:list')
