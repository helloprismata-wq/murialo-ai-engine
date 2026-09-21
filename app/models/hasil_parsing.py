from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base

class HasilParsing(Base):
    __tablename__ = "hasil_parsings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cv_id = Column(Integer, index=True, nullable=True)
    pelamar_id = Column(Integer, index=True, nullable=True)
    nama_file = Column(String(255), nullable=True)
    nama_lengkap = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    nomor_telepon = Column(String(50), nullable=True)
    skill_terdeteksi = Column(Text, nullable=True)
    riwayat_kerja = Column(Text, nullable=True)
    pendidikan = Column(Text, nullable=True)
    teks_mentah = Column(Text, nullable=True)
    diparse_pada = Column(DateTime, server_default=func.now())
    diperbarui_pada = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "cv_id": self.cv_id,
            "pelamar_id": self.pelamar_id,
            "nama_file": self.nama_file,
            "nama_lengkap": self.nama_lengkap,
            "email": self.email,
            "nomor_telepon": self.nomor_telepon,
            "skill_terdeteksi": self.skill_terdeteksi,
            "skill_list": [s.strip() for s in self.skill_terdeteksi.split(",") if s.strip()] if self.skill_terdeteksi else [],
            "riwayat_kerja": self.riwayat_kerja,
            "pendidikan": self.pendidikan,
            "diparse_pada": self.diparse_pada.isoformat() if self.diparse_pada else None,
            "diperbarui_pada": self.diperbarui_pada.isoformat() if self.diperbarui_pada else None,
        }
