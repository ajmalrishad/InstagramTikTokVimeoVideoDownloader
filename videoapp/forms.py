from django import forms
from .models import URL, Video
from urllib.parse import urlparse

class URLForm(forms.ModelForm):
    class Meta:
        model = URL
        fields = ['url']
        widgets = {
            'url': forms.URLInput(attrs={'placeholder': 'Enter URL here'}),
        }
        labels = {
            'url': 'URL',
        }


class VideoForm(forms.ModelForm):
    class Meta:
        model = Video
        fields = ['video']

