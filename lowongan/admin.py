from django.contrib import admin
from .models import Lowongan

@admin.register(Lowongan)
class LowonganAdmin(admin.ModelAdmin):
    list_display = ("posisi", "aktif", "dibuat_pada")
    list_filter = ("aktif",)
    search_fields = ("posisi", "keterampilan_dibutuhkan")
