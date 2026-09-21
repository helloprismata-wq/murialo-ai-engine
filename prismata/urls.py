from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('akun/', include('akun.urls')),
    path('resume/', include('resume.urls')),
    # Redirect root ke halaman daftar CV
    path('', RedirectView.as_view(url='/resume/', permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

