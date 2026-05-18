from django.db.models import Sum, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal

# PASTIKAN SEMUA MODEL INI DI-IMPORT DARI models.py
from .models import IuranPanen, PenjualanGabah, SimpanPinjam, Pengeluaran, BukuKas


class CashflowReport:
    """
    Class untuk generate Laporan Arus Kas berdasarkan periode.
    """
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def get_pemasukan(self):
        """Menghitung seluruh Kas Masuk"""
        # 1. Iuran Panen (Nilai Rp dari gabah yang disetor anggota)
        iuran = IuranPanen.objects.filter(
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('nilai_rp'), Decimal('0')))['total']

        # 2. Penjualan Gabah
        penjualan = PenjualanGabah.objects.filter(
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('total_rp'), Decimal('0')))['total']

        # 3. Simpanan Anggota (Uang masuk ke koperasi)
        simpanan = SimpanPinjam.objects.filter(
            tipe='simpanan',
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('jumlah_rp'), Decimal('0')))['total']

        # 4. Bunga Pinjaman 
        # Kita hitung di sisi Python untuk menghindari error database pada F() expression division
        pinjaman_qs = SimpanPinjam.objects.filter(
            tipe='pinjaman',
            tanggal__range=(self.start_date, self.end_date)
        )
        bunga = sum((p.jumlah_rp * p.bunga_persen / Decimal('100')) for p in pinjaman_qs)

        # 5. Buku Kas Manual (Kategori Lain-lain)
        kas_masuk_lainnya = BukuKas.objects.filter(
            tipe='masuk',
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('jumlah_rp'), Decimal('0')))['total']

        return {
            'iuran_panen': iuran,
            'penjualan_gabah': penjualan,
            'simpanan_anggota': simpanan,
            'bunga_pinjaman': bunga,
            'kas_masuk_lainnya': kas_masuk_lainnya,
            'total_pemasukan': iuran + penjualan + simpanan + bunga + kas_masuk_lainnya
        }

    def get_pengeluaran(self):
        """Menghitung seluruh Kas Keluar"""
        # 1. Pinjaman Anggota (Uang keluar dari koperasi)
        pinjaman = SimpanPinjam.objects.filter(
            tipe='pinjaman',
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('jumlah_rp'), Decimal('0')))['total']

        # 2. Pengeluaran Operasional
        pengeluaran = Pengeluaran.objects.filter(
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('jumlah_rp'), Decimal('0')))['total']

        # 3. Buku Kas Manual (Kategori Lain-lain)
        kas_keluar_lainnya = BukuKas.objects.filter(
            tipe='keluar',
            tanggal__range=(self.start_date, self.end_date)
        ).aggregate(total=Coalesce(Sum('jumlah_rp'), Decimal('0')))['total']

        return {
            'pinjaman_anggota': pinjaman,
            'pengeluaran_operasional': pengeluaran,
            'kas_keluar_lainnya': kas_keluar_lainnya,
            'total_pengeluaran': pinjaman + pengeluaran + kas_keluar_lainnya
        }

    def get_summary(self):
        """Mendapatkan ringkasan Cashflow"""
        pemasukan = self.get_pemasukan()
        pengeluaran = self.get_pengeluaran()
        saldo_bersih = pemasukan['total_pemasukan'] - pengeluaran['total_pengeluaran']

        return {
            'periode_mulai': self.start_date,
            'periode_selesai': self.end_date,
            'pemasukan': pemasukan,
            'pengeluaran': pengeluaran,
            'saldo_bersih': saldo_bersih,
        }