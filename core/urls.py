
from django.urls import path
from .views import query_code, generate_tests, upload_repository

urlpatterns = [
    path("query-code/", query_code, name="query_code"),
    path("generate-tests/", generate_tests, name="generate_tests"),
    path("upload-repo/", upload_repository, name="upload_repository"),
]

