from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import json

# Backend API base URL
BACKEND_API_URL = "http://127.0.0.1:8000"

@csrf_exempt
def home(request):
    """Render the modern home page with a sleek UI using Tailwind CSS."""
    return render(request, "index.html")

@csrf_exempt
def query_code(request):
    """Send a code-related query to the backend API."""
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get("query", "")
        response = requests.post(f"{BACKEND_API_URL}/query/", json={"prompt": user_query})
        return JsonResponse(response.json())
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def generate_tests(request):
    """Send a request to generate unit tests for provided code."""
    if request.method == "POST":
        data = json.loads(request.body)
        code_snippet = data.get("code", "")
        response = requests.post(f"{BACKEND_API_URL}/generate_tests/", json={"code_snippet": code_snippet})
        return JsonResponse(response.json())
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def upload_code(request):
    """Handle code file uploads."""
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        files = {"file": file}
        response = requests.post(f"{BACKEND_API_URL}/upload/", files=files)
        return JsonResponse(response.json())
    return JsonResponse({"error": "No file uploaded"}, status=400)
