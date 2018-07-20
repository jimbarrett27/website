from django.contrib import admin
from .models import Blog, BlogPost, Author, Topic

# Register your models here.
admin.site.register(Blog)
admin.site.register(BlogPost)
admin.site.register(Author)
admin.site.register(Topic)