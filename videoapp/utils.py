from django.contrib.sites import requests
from instaloader import Instaloader, Post


def get_video_info(video_link):
    try:
        L = Instaloader()
        post = Post.from_shortcode(L.context, video_link.split("/")[-2])
        # Fetch video thumbnail
        thumbnail = post._full_metadata_dict['thumbnail_src']
        response = requests.get(thumbnail)
        return response
    except:
        pass