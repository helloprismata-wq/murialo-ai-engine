"""
resume/views.py
===============
View untuk Modul 1 — Resume Parser.

URL yang tersedia:
  /resume/           → DaftarCVView  (lihat semua CV yang sudah diupload)
  /resume/upload/    → UploadCVView  (form upload CV baru)
  /resume/<id>/      → DetailCVView  (lihat hasil parsing CV)
  /resume/<id>/parse/ → ParseCVView  (trigger parsing manual)
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View

from .models import CV, HasilParsing
from .forms import FormUploadCV

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
class UploadCVView(View):
    """
    Tampilkan form upload CV dan proses file yang dikirim.
    Setelah upload berhasil, langsung jalankan parsing otomatis.
    """
    template_name = "resume/upload.html"

    def get(self, request):
        form = FormUploadCV()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = FormUploadCV(request.POST, request.FILES)
        if form.is_valid():
            cv = form.save(commit=False)
            cv.pelamar = request.user
            cv.save()
            messages.success(request, "File CV berhasil diunggah!")
            
            # Langsung parsing setelah upload
            try:
                from .parser import parse_cv
                parse_cv(cv)
                messages.success(request, "CV berhasil diparse secara otomatis!")
                return redirect("resume:detail", pk=cv.pk)
            except Exception as e:
                logger.exception(f"Parsing gagal untuk CV {cv.pk}: {e}")
                messages.warning(
                    request,
                    f"CV diunggah tapi parsing otomatis gagal: {e}. "
                    "Coba parse manual dari halaman detail."
                )
                return redirect("resume:detail", pk=cv.pk)
        
        return render(request, self.template_name, {"form": form})


@method_decorator(login_required, name="dispatch")
class DaftarCVView(View):
    """Tampilkan daftar semua CV milik user yang sedang login."""
    template_name = "resume/daftar.html"

    def get(self, request):
        cv_list = CV.objects.filter(pelamar=request.user).select_related("hasil_parsing")
        return render(request, self.template_name, {"cv_list": cv_list})


@method_decorator(login_required, name="dispatch")
class DetailCVView(View):
    """Tampilkan detail hasil parsing satu CV."""
    template_name = "resume/detail.html"

    def get(self, request, pk):
        cv = get_object_or_404(CV, pk=pk, pelamar=request.user)
        try:
            hasil = cv.hasil_parsing
        except HasilParsing.DoesNotExist:
            hasil = None
        return render(request, self.template_name, {"cv": cv, "hasil": hasil})


@method_decorator(login_required, name="dispatch")
class ParseCVView(View):
    """
    View untuk trigger parsing manual (jika parsing otomatis gagal).
    Hanya menerima POST request.
    """

    def post(self, request, pk):
        cv = get_object_or_404(CV, pk=pk, pelamar=request.user)
        try:
            from .parser import parse_cv
            parse_cv(cv)
            messages.success(request, "CV berhasil diparse ulang!")
        except Exception as e:
            logger.exception(f"Parsing manual gagal untuk CV {cv.pk}: {e}")
            messages.error(request, f"Parsing gagal: {e}")
        return redirect("resume:detail", pk=cv.pk)
