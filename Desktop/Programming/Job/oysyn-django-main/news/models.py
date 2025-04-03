from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify


class News(models.Model):
    title = models.CharField(
        _('title'), max_length=255,
        help_text=_('The news title.'),
    )
    excerpt = models.TextField(
        _('excerpt'), blank=True,
        help_text=_('Short summary.'),
    )
    text = models.TextField(
        _('text'), blank=True,
        help_text=_('The full content of the news article.'),
    )
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved = models.BooleanField(_('Is the news approved'), default=False)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    
class NewsImage(models.Model):
    news = models.ForeignKey(News, related_name='images', 
                             on_delete=models.CASCADE)
    image = models.ImageField(upload_to='news_gallery/',
                              help_text='Image for news')

    def __str__(self):
        return f"Image for {self.news.title}"
