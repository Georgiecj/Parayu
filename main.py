'''
import requests
import json
from pprint import pprint as pp
from Tools.scripts.summarize_stats import pretty

api_url = "http://10.10.207.13:8081/v1/chat/completions"

data = {
    "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
    "messages": [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What are some Web applications build using Django"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024,
    "stream": False
}


try:
    response = requests.post(api_url, json=data)
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        # print("Response JSON:", response.json())
        response = response.json()
        # pp(response)
        # pp(resp['choices']['message']['content'])
        pp(response['choices'][0]['message']['content'])
    else:
        print(f"Error: Unable to get a response. Status Code: {response.status_code}")
        print("Response Text:", response.text)
except Exception as e:
    print("An error occurred:", e)
'''

from django.shortcuts import render
from django.http import JsonResponse
import requests
from django.views.decorators.csrf import csrf_exempt
import json
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

# Backend API base URL for LLM
LLM_API_URL = "http://10.10.207.13:8081/v1/chat/completions"

UPLOAD_DIR = "uploaded_repos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@csrf_exempt
def home(request):
    """Render the modern home page with a sleek UI using Tailwind CSS."""
    return render(request, "index.html")

@csrf_exempt
def query_code(request):
    """Send a code-related query to the language model API."""
    if request.method == "POST":
        data = json.loads(request.body)
        user_query = data.get("query", "")
        payload = {
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "messages": [
                {"role": "system", "content": "You are an AI assistant that answers questions about code."},
                {"role": "user", "content": user_query}
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False
        }
        response = requests.post(LLM_API_URL, json=payload)
        resp = response.json()
        return resp['choices'][0]['message']['content']
        # return JsonResponse(response.json())
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def generate_tests(request):
    """Generate unit tests for provided code."""
    if request.method == "POST":
        data = json.loads(request.body)
        code_snippet = data.get("code", "")
        payload = {
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "messages": [
                {"role": "system", "content": "You are an AI assistant that generates unit tests for Python functions."},
                {"role": "user", "content": f"Generate unit tests for the following code:\n\n{code_snippet}"}
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": False
        }
        response = requests.post(LLM_API_URL, json=payload)
        return JsonResponse(response.json())
    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def upload_code(request):
    """Handle code file uploads."""
    if request.method == "POST" and request.FILES.get("file"):
        file = request.FILES["file"]
        file_path = os.path.join(UPLOAD_DIR, file.name)
        default_storage.save(file_path, ContentFile(file.read()))
        return JsonResponse({"message": "File uploaded successfully", "file": file.name})
    return JsonResponse({"error": "No file uploaded"}, status=400)

@csrf_exempt
def health_check(request):
    """Check if the backend API is running."""
    return JsonResponse({"status": "running"})



