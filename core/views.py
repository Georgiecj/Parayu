import os
import zipfile
import tempfile
import requests
import logging
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

MODEL_API_URL = "http://10.10.207.13:8081/v1/chat/completions"

def fetch_response(messages):
    """Helper function to call the model API."""
    data = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
        "stream": False
    }

    try:
        response = requests.post(MODEL_API_URL, json=data, timeout=15)
        response.raise_for_status()
        resp_json = response.json()

        if "choices" in resp_json and resp_json["choices"]:
            return resp_json["choices"][0]["message"]["content"]
        return "Error: No response content from model."

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to reach model API. {str(e)}"

@api_view(["POST"])
def query_code(request):
    user_query = request.data.get("query", "").strip()

    if not user_query:
        return HttpResponse("Error: Query is required.", content_type="text/plain", status=400)

    content = fetch_response([
        {"role": "system", "content": "You are an AI assistant that answers questions about anything."},
        {"role": "user", "content": user_query}
    ])

    return JsonResponse({"content": content})


@api_view(["POST"])
def generate_tests(request):
    code_snippet = request.data.get("code", "").strip()

    if not code_snippet:
        return JsonResponse({"error": "Code snippet is required."}, status=400)

    content = fetch_response([
        {"role": "system", "content": "Generate unit tests for the given Python function."},
        {"role": "user", "content": f"Generate unit tests for this code:\n\n```python\n{code_snippet}\n```"}
    ])

    return JsonResponse({"content": content})

@csrf_exempt
@api_view(["POST"])
def upload_repository(request):
    """Handles uploaded repository files: ZIP or individual Python files."""
    print("inside upload_repository")
    logger.debug(f"Request FILES: {request.FILES}")
    uploaded_files = request.FILES.getlist("repo")  # Handle multiple files
    if not uploaded_files:
        return JsonResponse({"error": "No files uploaded."}, status=400)
    temp_dir = tempfile.mkdtemp()  # Create temp dir to store files
    python_files = []

    for file in uploaded_files:
        if file.name.endswith(".zip"):  # If it's a ZIP file, extract it
            zip_path = os.path.join(temp_dir, file.name)
            with open(zip_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)

        elif file.name.endswith(".py"):  # If it's a Python file, store it directly
            file_path = os.path.join(temp_dir, file.name)
            with open(file_path, "wb") as f:
                for chunk in file.chunks():
                    f.write(chunk)

    # Find all Python files
    for root, _, files in os.walk(temp_dir):
        for file in files:
            if file.endswith(".py") and "test_" not in file:
                print("file",file)# Exclude existing test files
                file_path = os.path.join(root, file)
                with open(file_path, "r", encoding="utf-8") as f:
                    code_content = f.read()
                python_files.append({"file": file, "content": code_content})
    print("len of python_files:", len(python_files))
    if not python_files:
        return JsonResponse({"error": "No Python files found in repository."}, status=400)

    # Generate unit tests for each Python file
    unit_tests = {}
    for py_file in python_files:
        print(f"hitting LLM")
        test_content = fetch_response([
            {"role": "system", "content": "Generate unit tests for the given Python module."},
            {"role": "user", "content": f"Generate unit tests for this module:\n\n```python\n{py_file['content']}\n```"}
        ])
        unit_tests[py_file["file"]] = test_content
    print("finished unit tests")
    return JsonResponse({"unit_tests": unit_tests})
