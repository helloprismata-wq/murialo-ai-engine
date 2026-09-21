from django.contrib import admin
from .models import CV, HasilParsing


class HasilParsingInline(admin.StackedInline):
    model = HasilParsing
    extra = 0
    readonly_fields = ("diparse_pada", "diperbarui_pada")
    fields = (
        "nama_lengkap", "email", "nomor_telepon",
        "skill_terdeteksi", "riwayat_kerja", "pendidikan",
        "diparse_pada", "diperbarui_pada",
    )


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ("pelamar", "nama_file", "sudah_diparse", "diunggah_pada")
    list_filter = ("sudah_diparse",)
    search_fields = ("pelamar__username", "nama_file")
    readonly_fields = ("diunggah_pada",)
    inlines = [HasilParsingInline]
    actions = ["parse_semua"]

    @admin.action(description="Parse ulang CV yang dipilih")
    def parse_semua(self, request, queryset):
        berhasil = 0
        gagal = 0
        for cv in queryset:
            try:
                from .parser import parse_cv
                parse_cv(cv)
                berhasil += 1
            except Exception:
                gagal += 1
        self.message_user(
            request,
            f"Parsing selesai: {berhasil} berhasil, {gagal} gagal."
        )


@admin.register(HasilParsing)
class HasilParsingAdmin(admin.ModelAdmin):
    list_display = ("cv", "nama_lengkap", "email", "diparse_pada")
    search_fields = ("nama_lengkap", "email", "skill_terdeteksi")
    readonly_fields = ("diparse_pada", "diperbarui_pada")
