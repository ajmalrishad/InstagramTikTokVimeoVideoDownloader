
import base64
import os
import subprocess

import requests
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from instaloader import Instaloader, Post
from tiktokapipy.api import TikTokAPI

from .forms import URLForm


@csrf_exempt
def enter_url(request):
    if request.method == 'POST':
        form = URLForm(request.POST)

        if form.is_valid():
            url = form.cleaned_data['url']
            if url.startswith("https://www.instagram.com"):
                try:
                    response, title = get_video_info(url)
                    video_url = url
                    return render(request, 'success_page.html', {'title': title,'response': response, 'video_url': video_url})
                except Exception as e:
                    return HttpResponse("An error occurred while processing the URL because of too many attempt please try again later")

            if url.startswith("https://vimeo.com/"):
                try:
                    thumbnail_url, video_title = get_vimeo_video_info(url)
                    video_url = url
                    return render(request, 'vimeo_sucess_page.html',{'thumbnail_url': thumbnail_url, 'video_title':video_title, 'video_url':video_url})
                except Exception as e:
                    print("error",str(e))
                    return HttpResponse("An error occurred while processing the URL: {}".format(str(e)), status=500)
            if url.startswith("https://www.tiktok.com/"):
                try:
                    thumbnail_url, title = get_video_thumbnail(url)
                    video_url = url
                    return render(request, 'tiktok_success_page.html',{'thumbnail_url':thumbnail_url,'title': title, 'video_url': video_url })
                except Exception as e:
                    print("error",str(e))
                    return HttpResponse("An error occurred while processing the URL: {}".format(str(e)), status=500)
            else:
                form = URLForm()
                return render(request, 'enter_url.html', {'form': form})
        else:
            return HttpResponse("Invalid form data", status=400)
    else:
        # If it's a GET request or a failed form submission, initialize the form with empty fields
        form = URLForm()

    return render(request, 'enter_url.html', {'form': form})


@csrf_exempt
def get_video_info(url):
    try:
        L = Instaloader()
        post = Post.from_shortcode(L.context, url.split("/")[-2])
        # Fetch video thumbnail
        thumbnail = post._full_metadata_dict['thumbnail_src']
        response = requests.get(thumbnail)
        image_data = base64.b64encode(response.content).decode('utf-8')  # Convert image content to base64
        title = post._full_metadata['edge_media_to_caption']['edges'][0]['node']['text']
        return image_data, title
    except Exception as e:
        raise e

@csrf_exempt
def show_success_page(request,url):
    try:
        response, title = get_video_info(url)
        return render(request, 'success_page.html', {'title': title, 'response': response})
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})


@csrf_exempt
def download_video(request):
    try:
        url = request.GET.get('url')

        if not url:
            return HttpResponse("Missing 'url' parameter.", status=400)

        # Run yt-dlp to download the video
        command = ['yt-dlp', '--get-url', url]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return HttpResponse(f"Error downloading video: {stderr.decode()}", status=500)

        video_url = stdout.decode().strip()

        # Prepare HTTP response with video URL
        response = HttpResponse()
        response['Content-Type'] = 'text/plain'
        response.write(video_url)

        return response

    except Exception as e:
        return HttpResponse(f"Error downloading video: {e}", status=500)


def get_vimeo_video_info(url):
    try:
        video_id = url.split('/')[-1]
        print("video_id", video_id)
        response = requests.get(f"https://vimeo.com/api/v2/video/{video_id}.json")

        if response.status_code == 200 and response.headers['Content-Type'] == 'application/json':
            video_data = response.json()[0]
            video_title = video_data.get('title')
            thumbnail_url = video_data.get('thumbnail_large')
            return thumbnail_url, video_title
        else:
            raise ValueError(f"Failed to fetch thumbnail for video: {url}")
    except Exception as e:
        raise e

def download_vimeo_video(request):
    try:
        url = request.GET.get('url')

        if not url:
            return HttpResponse("Missing 'url' parameter.", status=400)

        # Run yt-dlp to download the video
        command = ['yt-dlp', '--merge-output-format', 'mp4', url]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            return HttpResponse(f"Error downloading video: {stderr.decode()}", status=500)

        # Save the downloaded video to a temporary file
        temp_file = "temp_video.mp4"
        with open(temp_file, "wb") as f:
            f.write(stdout)

        # Prepare HTTP response with video content
        with open(temp_file, "rb") as f:
            video_content = f.read()

        response = HttpResponse(video_content, content_type='video/mp4')
        response['Content-Disposition'] = 'attachment; filename="vimeo_video.mp4"'

        # Delete the temporary file
        os.remove(temp_file)

        return response

    except Exception as e:
        return HttpResponse(f"Error downloading Vimeo video: {e}", status=500)
    
@csrf_exempt
def vimeo_success_page(request, url):
    try:
        thumbnail_url, video_title = get_vimeo_video_info(url)
        video_url = download_vimeo_video(url)
        return render(request, 'vimeo_sucess_page.html',{'thumbnail_url':thumbnail_url,'video_title':video_title, 'video_url':video_url})
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})

#tiktok functions
@csrf_exempt
def get_video_thumbnail(url):
    with TikTokAPI() as api:
        # Fetch video information
        video = api.video(url)
        # Access the thumbnail URL from the video object
        thumbnail_url = video.video.cover
        title = video.desc
        return thumbnail_url,title

def tiktok_download(request):
    try:
        # Extract the URL parameter from the request
        url = request.GET.get('url')
        print("Attempting to download TikTok video from URL:", url)

        # Initialize TikTokAPI
        with TikTokAPI() as api:
            # Fetch video information
            video = api.video(url)
            if video and hasattr(video, 'video') and hasattr(video.video, 'download_addr') and video.video.download_addr:
                # Download the video content
                video_content = download_video_content(video, api)
                if video_content:
                    # Set content disposition to force download
                    response = HttpResponse(video_content, content_type='video/mp4')
                    response['Content-Disposition'] = 'attachment; filename="tiktok_video.mp4"'
                    messages.success(request, "TikTok Video downloaded successfully")
                    return response  # Return the HttpResponse object
                else:
                    messages.error("Failed to download TikTok video", status=500)
            else:
                messages.error("Failed to download TikTok video: Invalid response", status=500)
    except Exception as e:
        print(f"Error downloading video: {e}")
        messages.error(f"Error downloading TikTok video: {e}", status=500)
        return redirect('enter_url')


def download_video_content(video, api):
    try:
        cookies = {cookie["name"]: cookie["value"] for cookie in api.context.cookies() if cookie["name"] == "tt_chain_token"}
        with requests.Session() as session:
            resp = session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}, cookies=cookies)
            if resp.status_code == 200:
                return resp.content
    except Exception as e:
        print("Error downloading video content:", e)
        return None


def tiktok_success_page(request,url):
    try:
       print("Tiktok Success page works")
       thumbnail_url,title = get_video_thumbnail(url)
       return render(request, 'tiktok_sucess_page.html',{'thumbnail_url':thumbnail_url,'title': title })
    except Exception as e:
        return render(request, 'error_page.html', {'error_message': str(e)})

