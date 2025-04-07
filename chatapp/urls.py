from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

def home(request):
    return render(request, "index.html")

def upload_page(request):
    return render(request, "upload.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("", home, name="home"),
    path("upload.html", upload_page, name="upload_page"),
    path("index.html", home, name="home"),

]
