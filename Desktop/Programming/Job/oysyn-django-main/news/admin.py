from django.contrib import admin
from .models import News, NewsImage

class NewsImageInline(admin.TabularInline):
    model = NewsImage
    extra = 1  # Number of empty forms to display

class NewsAdmin(admin.ModelAdmin):
    inlines = [NewsImageInline]
    list_display = ('title', 'created_at', 'updated_at')  # Optional: display these fields in the list view
    prepopulated_fields = {'slug': ('title',)}  # Automatically populate the slug from the title

admin.site.register(News, NewsAdmin)
admin.site.register(NewsImage)
