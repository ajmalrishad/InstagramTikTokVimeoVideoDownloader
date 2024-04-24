from django.db import models

# Create your models here.

class URL(models.Model):
    url = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.url


class Video(models.Model):
     video = models.ImageField(upload_to = 'video/')

     def __str__(self):
         return self.name







