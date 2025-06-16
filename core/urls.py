
from django.urls import path
from .views import query_code, generate_tests, upload_repository, execute_code, fetch_api, intelligent_faq

urlpatterns = [
    path("query-code/", query_code, name="query_code"),
    path("generate-tests/", generate_tests, name="generate_tests"),
    path("upload-repo/", upload_repository, name="upload_repository"),
    path("execute-code/", execute_code, name="execute_code"),
    path("fetch-api/", fetch_api, name="fetch_api"),
    path("intelligent-faq/", intelligent_faq, name="intelligent_faq")
]

