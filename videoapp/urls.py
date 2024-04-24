from django.urls import path
from . import views




urlpatterns = [
    path('', views.enter_url, name='enter_url'),
    path('show_success_page',views.show_success_page,name='show_success_page'),
    path('download_video', views.download_video, name='download_video'),
    path('vimeo_success_page',views.vimeo_success_page,name='vimeo_success_page'),
    path('download_vimeo_video',views.download_vimeo_video,name='download_vimeo_video'),
    path('tiktok_download',views.tiktok_download,name='tiktok_download'),
    path('tiktok_success_page',views.tiktok_success_page,name='tiktok_success_page'),



]