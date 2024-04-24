from django.contrib import admin

# Register your models here.

from .models import URL, Video

admin.site.register(URL)
admin.site.register(Video)


