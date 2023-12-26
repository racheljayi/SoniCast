from django.shortcuts import render, redirect
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
import environ, requests, json, base64

from .models import User
from . import util

env = environ.Env()
environ.Env.read_env()

scopes = "ugc-image-upload playlist-modify-private playlist-modify-public user-top-read"
REDIRECT_URI = "http://localhost:8000/callback"

# load home page
def index(request):
    return render(request, "index.html")

# request user authorization
@api_view(['GET', 'POST'])
def login(request):
    oauth = {
        'client_id': env("SPOTIFY_CLIENT_ID"),
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': scopes,
    }
    url = requests.get('https://accounts.spotify.com/authorize', oauth).url
    try:
      return redirect(url)
    except:
      return Response({"Message": "Cannot be authorized"}, status=status.HTTP_400_BAD_REQUEST)

# request & store access token and user location
def callback(request):
     code = request.GET.get('code')

     # get access token
     #try:
     params = {
             'grant_type': "authorization_code",
             'code': code,
             'redirect_uri': REDIRECT_URI
         }
     credentials = f'{env("SPOTIFY_CLIENT_ID")}:{env("SPOTIFY_CLIENT_SECRET")}'.encode('utf-8')
     headers = {
             'Authorization': 'Basic ' + base64.b64encode(credentials).decode('utf-8'),
             'content-type': 'application/x-www-form-urlencoded',
         }
     token = requests.post("https://accounts.spotify.com/api/token", params=params, headers=headers).json()
         # store current user_id in session
     request.session["user_id"] = util.update_user_token(token)
     #except:
        #raise Http404("Authorization failed")
     
     # get user ip 
     from ipware import get_client_ip
     client_ip, is_routable = get_client_ip(request)
     if client_ip is None:
         raise Http404("Accessing location failed")
     else:
         if is_routable:
             print(client_ip)
         else: # TODO 
             # remove client_ip for testing & replace with proper error message
             print("not routable")
             client_ip = '47.189.84.176'
    
    # get location information
     try:
         params = {
             'key': env("WEATHER_API_KEY"),
             'q': client_ip
         }
         ip_information = requests.post("https://api.weatherapi.com/v1/ip.json", params=params).json()
         request.session["user_id"] = util.update_user_location(ip_information, request.session["user_id"])
     except: 
         raise Http404("Weather retrival failed")

     return redirect("/results/")

# display results
def results(request):
    # get recommendations
    forecast = util.request_forecast(request.session["user_id"])
    print(forecast)
    return render(request, "results.html")    