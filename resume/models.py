from django.db import models
from akun.models import User


class CV(models.Model):
    """
    Menyimpan file CV yang diunggah oleh pelamar.
    """
    pelamar = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cv_list"
    )
    file_cv = models.FileField(
        upload_to="cv_uploads/",
        verbose_name="File CV (PDF/DOCX)",
    )
    nama_file = models.CharField(max_length=255, blank=True)
    diunggah_pada = models.DateTimeField(auto_now_add=True)
    sudah_diparse = models.BooleanField(default=False)

    class Meta:
        verbose_name = "CV"
        verbose_name_plural = "CV"
        ordering = ["-diunggah_pada"]

    def __str__(self):
        return f"CV {self.pelamar.username} - {self.diunggah_pada.strftime('%d/%m/%Y')}"

    def save(self, *args, **kwargs):
        if self.file_cv and not self.nama_file:
            self.nama_file = self.file_cv.name.split("/")[-1]
        super().save(*args, **kwargs)


class HasilParsing(models.Model):
    """
    Menyimpan hasil ekstraksi spaCy dari sebuah CV.
    Tabel ini menjadi INPUT untuk Modul 2 dan Modul 3.
    """
    cv = models.OneToOneField(CV, on_delete=models.CASCADE, related_name="hasil_parsing")
    
    # --- Entitas yang diekstrak spaCy ---
    nama_lengkap = models.CharField(max_length=200, blank=True, verbose_name="Nama Lengkap")
    email = models.EmailField(blank=True, verbose_name="Email")
    nomor_telepon = models.CharField(max_length=30, blank=True, verbose_name="No. Telepon")
    
    # Disimpan sebagai teks JSON-like, dipisah newline/koma
    skill_terdeteksi = models.TextField(blank=True, verbose_name="Skill Terdeteksi")
    riwayat_kerja = models.TextField(blank=True, verbose_name="Riwayat Kerja")
    pendidikan = models.TextField(blank=True, verbose_name="Pendidikan")
    
    # Teks mentah hasil ekstraksi dari PDF/DOCX
    teks_mentah = models.TextField(blank=True, verbose_name="Teks Mentah CV")
    
    diparse_pada = models.DateTimeField(auto_now_add=True)
    diperbarui_pada = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hasil Parsing CV"
        verbose_name_plural = "Hasil Parsing CV"

    def __str__(self):
        return f"Parsing CV {self.cv.pelamar.username}"

    def daftar_skill(self):
        """Kembalikan list skill hasil parsing (sudah lowercase)."""
        if not self.skill_terdeteksi:
            return []
        return [s.strip().lower() for s in self.skill_terdeteksi.split(",") if s.strip()]
