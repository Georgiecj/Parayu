from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render

def home(request):
    return render(request, "index.html")

def upload_page(request):
    return render(request, "upload.html")

def devtools_page(request):
    return render(request, "devtools.html")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
    path("", home, name="home"),
    path("parayu.ai/upload", upload_page, name="upload_page"),
    path("parayu.ai", home, name="home"),
    path("parayu.ai/devtools", devtools_page, name="devtools_page"),
    path("parayu.ai/intelligent-faq", lambda r: render(r, "intelligent_faq.html"), name="intelligent_faq_page")
]
