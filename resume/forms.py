from django import forms
from .models import CV

# Format file yang diterima sistem
EKSTENSI_DOKUMEN = (".pdf", ".docx", ".doc")
EKSTENSI_GAMBAR  = (".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif")
SEMUA_EKSTENSI   = EKSTENSI_DOKUMEN + EKSTENSI_GAMBAR


class FormUploadCV(forms.ModelForm):
    """
    Form upload CV — mendukung:
      • Dokumen : PDF, DOCX, DOC
      • Gambar  : JPG, JPEG, PNG, WEBP, BMP, TIFF
        (teks diekstrak via OCR pytesseract secara otomatis)
    """

    class Meta:
        model = CV
        fields = ["file_cv"]
        labels  = {"file_cv": "Pilih File CV atau Foto CV"}
        widgets = {
            "file_cv": forms.FileInput(attrs={
                "accept": ".pdf,.docx,.doc,.jpg,.jpeg,.png,.webp,.bmp,.tiff,.tif",
                "class": "file-input",
                "id": "input-file-cv",
            }),
        }

    def clean_file_cv(self):
        """Validasi file: cek ekstensi dan ukuran (maks 10 MB)."""
        file = self.cleaned_data.get("file_cv")
        if file:
            nama = file.name.lower()
            if not any(nama.endswith(ext) for ext in SEMUA_EKSTENSI):
                raise forms.ValidationError(
                    "Format tidak valid. Gunakan PDF, DOCX, JPG, PNG, atau WEBP."
                )
            ukuran_maks = 10 * 1024 * 1024  # 10 MB
            if file.size > ukuran_maks:
                raise forms.ValidationError(
                    f"File terlalu besar ({file.size // 1024} KB). Maksimal 10 MB."
                )
        return file

