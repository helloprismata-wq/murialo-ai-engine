from django.urls import path
from . import views

app_name = "resume"

urlpatterns = [
    path("", views.DaftarCVView.as_view(), name="daftar"),
    path("upload/", views.UploadCVView.as_view(), name="upload"),
    path("<int:pk>/", views.DetailCVView.as_view(), name="detail"),
    path("<int:pk>/parse/", views.ParseCVView.as_view(), name="parse"),
]
