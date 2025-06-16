import os
import zipfile

import logging
import subprocess
import sys
import base64
from tempfile import TemporaryDirectory
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import faiss, pickle
from sentence_transformers import SentenceTransformer
from rest_framework.decorators import api_view
from django.http import JsonResponse
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

MODEL_API_URL = "http://10.10.207.13:8081/v1/chat/completions"
EMBEDDING_MODEL_PATH = "models/all-MiniLM-L6-v2"
INDEX_PATH = "faiss_index.bin"
DOC_STORE_PATH = "doc_texts.pkl"
# Load once
index = faiss.read_index(INDEX_PATH)
with open(DOC_STORE_PATH, "rb") as f:
    data = pickle.load(f)
texts, metadatas = data["texts"], data["metadatas"]
embedder = SentenceTransformer(EMBEDDING_MODEL_PATH)


def rag_query(user_question, top_k=7):
    logger.debug(f"Embedding question: {user_question}")
    q_emb = embedder.encode([user_question])
    D, I = index.search(q_emb, k=top_k)

    logger.debug(f"FAISS distances: {D[0]}")

    seen = set()
    context_chunks = []
    source_refs = []

    for i in I[0]:
        if i not in seen:
            seen.add(i)
            chunk = texts[i].strip()
            if chunk:
                context_chunks.append(chunk)
                source_refs.append(metadatas[i])

    context = "\n\n".join(context_chunks)
    return context, source_refs

@api_view(["POST"])
def intelligent_faq(request):
    user_q = request.data.get("query", "").strip()
    chat_history = request.data.get("history", [])

    if not user_q:
        return JsonResponse({"error": "Query is required."}, status=400)

    logger.info(f"Received user query: {user_q}")
    logger.info(f"Received chat history for iDEC: {chat_history}")

    context, sources = rag_query(user_q)

    prompt_messages = [
        {"role": "system", "content": (
            "You are Parayu, an intelligent and helpful support assistant. "
            "You will be given documentation excerpts and a user question. "
            "If the answer isn't present, say you don't know."
        )}
    ]

    for msg in chat_history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            # Only add 'user' and 'model' roles from history for conversation flow
            if msg["role"] in ["user", "model"]:
                prompt_messages.append({"role": msg["role"], "content": msg["content"]})
    if context:
        prompt_messages.append({"role": "system", "content": f"Documentation context:\n{context}"})
    else:
        prompt_messages.append({"role": "system", "content": "No relevant documentation found for the current query."})
    prompt_messages.append({"role": "user", "content": user_q})
    logger.info(f"Sending messages to model for iDEC: {prompt_messages}")

    try:
        logger.debug("Sending request to model...")
        resp = requests.post(MODEL_API_URL, json={
            "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
            "messages": prompt_messages,
            "temperature": 0.2,
            "max_tokens": 2048,
            "stream": False
        }, timeout=180)
        result = resp.json()
        answer = result["choices"][0]["message"]["content"]

    except Exception as e:
        logger.error(f"Model API error: {e}")
        return JsonResponse({
            "answer": "There was an issue contacting the language model.",
            "error": str(e)
        }, status=500)

    if not context:
        answer = "Sorry, I couldn’t find enough relevant information in the documentation."

    return JsonResponse({
        "answer": answer,
        "sources": sources
    })

def fetch_response(messages):
    """Helper function to call the model API."""
    data = {
        "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False
    }

    try:
        response = requests.post(MODEL_API_URL, json=data, timeout=180)
        response.raise_for_status()
        resp_json = response.json()

        if "choices" in resp_json and resp_json["choices"]:
            return resp_json["choices"][0]["message"]["content"]
        return "Error: No response content from model."

    except requests.exceptions.RequestException as e:
        return f"Error: Failed to reach model API. {str(e)}"

@api_view(["POST"])
def execute_code(request):
    code = request.data.get("code", "")
    language = request.data.get("language", "python")

    if not code:
        return JsonResponse({"error": "Code is required."}, status=400)

    try:
        if language == "python":
            result = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return JsonResponse({
                "stdout": result.stdout,
                "stderr": result.stderr
            })

        elif language == "javascript":
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return JsonResponse({
                "stdout": result.stdout,
                "stderr": result.stderr
            })

        else:
            return JsonResponse({"error": "Unsupported language."}, status=400)

    except subprocess.TimeoutExpired:
        return JsonResponse({"error": "Code execution timed out."}, status=500)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(["POST"])
def fetch_api(request):
    url = request.data.get("url")
    method = request.data.get("method", "GET").upper()
    headers = request.data.get("headers", {})
    payload = request.data.get("payload", {})
    if not url:
        return JsonResponse({"error": "URL is required."}, status=400)
    try:
        response = requests.request(method, url, headers=headers, json=payload, timeout=10)
        return JsonResponse({
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "body": response.text
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

@api_view(["POST"])
def query_code(request):
    user_query = request.data.get("query", "").strip()
    chat_history = request.data.get("history", [])
    logger.info(f"Received query: {user_query}")
    logger.info(f"Received chat history: {chat_history}")
    if not user_query:
        return HttpResponse("Error: Query is required.", content_type="text/plain", status=400)
    messages = [
        {"role": "system", "content": "You are an AI assistant named 'Parayu' developed by Georgie, designed to provide answers on anything."}
    ]
    for msg in chat_history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            if msg["role"] in ["user", "model"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_query})
    logger.info(f"Sending messages to AI: {messages}")
    content = fetch_response(messages)
    return JsonResponse({"content": content})


@api_view(["POST"])
def generate_tests(request):
    code_snippet = request.data.get("code", "").strip()
    if not code_snippet:
        return JsonResponse({"error": "Code snippet is required."}, status=400)
    content = fetch_response([
        {"role": "system", "content": "Generate unit tests for the given Python file. Return only the tests, nothing else."},
        {"role": "user", "content": f"Generate unit tests for this code:\n\n```python\n{code_snippet}\n```"}
    ])
    return JsonResponse({"content": content})

@csrf_exempt
@api_view(["POST"])
def upload_repository(request):
    """Handles uploaded repository files or Git URL and returns unit tests + zip."""
    logger.info("inside upload_repository")
    uploaded_files = request.FILES.getlist("repo")
    git_url = request.data.get("gitUrl")
    if not uploaded_files and not git_url:
        return JsonResponse({"error": "No files or Git URL provided."}, status=400)
    with TemporaryDirectory() as temp_dir:
        repo_dir = os.path.join(temp_dir, "repo")
        os.makedirs(repo_dir, exist_ok=True)
        output_dir = os.path.join(temp_dir, "unit_tests")
        os.makedirs(output_dir, exist_ok=True)
        python_files = []
        # --- Handle Git repo ---
        if git_url:
            # git_url_with_creds = extract_credentials(git_url)
            logger.info(f"Git URL: {git_url}")
            try:
                result = subprocess.run(
                    ["git", "clone", git_url, repo_dir],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(f"Git clone output: {result.stdout}")
            except subprocess.CalledProcessError as e:
                logger.error(f"Git clone failed with error: {e.stderr}")
                return JsonResponse({"error": f"Git clone failed: {e.stderr}"}, status=400)
        # --- Handle uploaded files ---
        elif uploaded_files:
            for file in uploaded_files:
                if file.name.endswith(".zip"):
                    zip_path = os.path.join(repo_dir, file.name)
                    with open(zip_path, "wb") as f:
                        for chunk in file.chunks():
                            f.write(chunk)
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(repo_dir)
                elif file.name.endswith(".py"):
                    file_path = os.path.join(repo_dir, file.name)
                    with open(file_path, "wb") as f:
                        for chunk in file.chunks():
                            f.write(chunk)
        # --- Collect Python files ---
        for root, _, files in os.walk(repo_dir):
            for file in files:
                if file.endswith(".py") and "test_" not in file:
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        code_content = f.read()
                    python_files.append({"file": file, "content": code_content})
        if not python_files:
            return JsonResponse({"error": "No Python files found."}, status=400)
        # --- Generate Unit Tests ---
        unit_tests_data = {}
        for py_file in python_files:
            logger.info(f"Generating unit test for {py_file['file']}")
            try:
                test_content = fetch_response([
                    {"role": "system", "content": "Generate unit tests for the given Python module. Return only the tests, nothing else."},
                    {"role": "user", "content": f"Generate unit tests for this module:\n\n```python\n{py_file['content']}\n```"}
                ])
            except Exception as e:
                logger.error(f"Error in fetch_response: {e}")
                return JsonResponse({"error": f"Error generating unit tests: {e}"}, status=500)
            test_file_name = f"test_{py_file['file']}"
            test_file_path = os.path.join(output_dir, test_file_name)
            with open(test_file_path, "w", encoding="utf-8") as f:
                f.write(test_content)
            unit_tests_data[py_file['file']] = test_content
        # --- Zip the generated test files ---
        zip_path = os.path.join(temp_dir, "unit_tests.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(output_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arc_name = os.path.relpath(file_path, output_dir)
                    zipf.write(file_path, arc_name)
        logger.info("Unit tests generated and zipped.")
        # --- Return the response ---
        with open(zip_path, "rb") as zip_file:
            zip_content = zip_file.read()
        zip_content_base64 = base64.b64encode(zip_content).decode('utf-8')
        return JsonResponse({
            "unit_tests": unit_tests_data,
            "zip_content": zip_content_base64
        }, content_type='application/json')
