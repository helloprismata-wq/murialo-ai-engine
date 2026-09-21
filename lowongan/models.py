from django.db import models

class Lowongan(models.Model):
    """Model lowongan kerja yang akan dicocokkan dengan CV pelamar."""
    posisi = models.CharField(max_length=200, verbose_name="Posisi")
    deskripsi = models.TextField(verbose_name="Deskripsi Pekerjaan")
    kualifikasi = models.TextField(verbose_name="Kualifikasi")
    keterampilan_dibutuhkan = models.TextField(
        help_text="Pisahkan dengan koma. Contoh: Python, Django, SQL",
        verbose_name="Keterampilan yang Dibutuhkan"
    )
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    aktif = models.BooleanField(default=True, verbose_name="Aktif")

    class Meta:
        verbose_name = "Lowongan"
        verbose_name_plural = "Lowongan"
        ordering = ["-dibuat_pada"]

    def __str__(self):
        return self.posisi

    def daftar_skill(self):
        """Kembalikan list skill yang dibutuhkan."""
        return [s.strip().lower() for s in self.keterampilan_dibutuhkan.split(",") if s.strip()]
