from django.contrib import admin
from .models import Anggota, HargaGabah, IuranPanen, SimpanPinjam, PenjualanGabah, Pengeluaran


@admin.register(Anggota)
class AnggotaAdmin(admin.ModelAdmin):
    list_display = ['nama', 'nik', 'telepon', 'status', 'tanggal_bergabung']
    list_filter = ['status']
    search_fields = ['nama', 'nik']


@admin.register(HargaGabah)
class HargaGabahAdmin(admin.ModelAdmin):
    list_display = ['tanggal', 'harga_per_100kg', 'catatan']
    ordering = ['-tanggal']


@admin.register(IuranPanen)
class IuranPanenAdmin(admin.ModelAdmin):
    list_display = ['anggota', 'periode', 'jumlah_kg', 'harga_per_100kg', 'nilai_rp', 'tanggal']
    list_filter = ['periode', 'tanggal']
    search_fields = ['anggota__nama']


@admin.register(SimpanPinjam)
class SimpanPinjamAdmin(admin.ModelAdmin):
    list_display = ['anggota', 'tipe', 'jumlah_rp', 'bunga_persen', 'tanggal', 'status']
    list_filter = ['tipe', 'status', 'tanggal']
    search_fields = ['anggota__nama']


@admin.register(PenjualanGabah)
class PenjualanGabahAdmin(admin.ModelAdmin):
    list_display = ['tanggal', 'pembeli', 'jumlah_kg', 'harga_per_100kg', 'total_rp']
    list_filter = ['tanggal']
    search_fields = ['pembeli']


@admin.register(Pengeluaran)
class PengeluaranAdmin(admin.ModelAdmin):
    list_display = ['tanggal', 'kategori', 'keterangan', 'jumlah_rp']
    list_filter = ['kategori', 'tanggal']
