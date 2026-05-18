from django.db import models
from django.conf import settings
from decimal import Decimal


class Anggota(models.Model):
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('nonaktif', 'Non-Aktif'),
    ]
    nama = models.CharField(max_length=200, verbose_name='Nama Lengkap')
    nik = models.CharField(max_length=20, unique=True, verbose_name='NIK')
    alamat = models.TextField(blank=True, verbose_name='Alamat')
    telepon = models.CharField(max_length=20, blank=True, verbose_name='No. Telepon')
    tanggal_bergabung = models.DateField(auto_now_add=True, verbose_name='Tanggal Bergabung')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif', verbose_name='Status')

    class Meta:
        ordering = ['nama']
        verbose_name = 'Anggota'
        verbose_name_plural = 'Anggota'

    def __str__(self):
        return self.nama

    @property
    def total_simpanan(self):
        return self.simpanpinjam_set.filter(
            tipe='simpanan', status='aktif'
        ).aggregate(total=models.Sum('jumlah_rp'))['total'] or 0

    @property
    def total_pinjaman(self):
        return self.simpanpinjam_set.filter(
            tipe='pinjaman', status='aktif'
        ).aggregate(total=models.Sum('jumlah_rp'))['total'] or 0

    @property
    def total_iuran_kg(self):
        return self.iuranpanen_set.aggregate(
            total=models.Sum('jumlah_kg')
        )['total'] or 0


class HargaGabah(models.Model):
    tanggal = models.DateField(verbose_name='Tanggal Berlaku')
    harga_per_100kg = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Harga per 100 kg (Rp)'
    )
    catatan = models.TextField(blank=True, verbose_name='Catatan Khusus')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Harga Gabah'
        verbose_name_plural = 'Harga Gabah'

    def __str__(self):
        return f'Rp {self.harga_per_100kg:,.0f}/100kg ({self.tanggal})'

    @staticmethod
    def get_harga_terbaru():
        obj = HargaGabah.objects.first()
        return obj.harga_per_100kg if obj else 0
    
class IuranPanen(models.Model):
    anggota = models.ForeignKey(Anggota, on_delete=models.CASCADE, verbose_name='Anggota')
    periode = models.CharField(max_length=50, verbose_name='Periode')
    jumlah_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Jumlah (kg)')
    tanggal = models.DateField(verbose_name='Tanggal Iuran')
    harga_per_100kg = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Harga per 100 kg (Rp)'
    )
    nilai_rp = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Nilai (Rp)',
        default=Decimal('0.00'),
        help_text='Otomatis dihitung: (jumlah_kg / 100) x harga_per_100kg'
    )
    keterangan = models.TextField(blank=True, default='', verbose_name='Keterangan')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Iuran Panen Gabah'
        verbose_name_plural = 'Iuran Panen Gabah'

    def __str__(self):
        return f'{self.anggota.nama} - {self.periode} - {self.jumlah_kg} kg'

    def save(self, *args, **kwargs):
        from decimal import Decimal
        if self.jumlah_kg and self.harga_per_100kg:
            self.nilai_rp = (self.jumlah_kg / Decimal('100')) * self.harga_per_100kg
        super().save(*args, **kwargs)

class SimpanPinjam(models.Model):
    TIPE_CHOICES = [
        ('simpanan', 'Simpanan'),
        ('pinjaman', 'Pinjaman'),
    ]
    STATUS_CHOICES = [
        ('aktif', 'Aktif'),
        ('lunas', 'Lunas'),
    ]
    anggota = models.ForeignKey(Anggota, on_delete=models.CASCADE, verbose_name='Anggota')
    tipe = models.CharField(max_length=10, choices=TIPE_CHOICES, verbose_name='Tipe')
    jumlah_rp = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Jumlah (Rp)')
    bunga_persen = models.DecimalField(
        max_digits=5, decimal_places=2, default=0, verbose_name='Bunga (%)'
    )
    tanggal = models.DateField(verbose_name='Tanggal')
    jatuh_tempo = models.DateField(null=True, blank=True, verbose_name='Jatuh Tempo')
    keterangan = models.TextField(blank=True, verbose_name='Keterangan')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='aktif', verbose_name='Status')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Simpan Pinjam'
        verbose_name_plural = 'Simpan Pinjam'

    def __str__(self):
        return f'{self.anggota.nama} - {self.get_tipe_display()} - Rp {self.jumlah_rp:,.0f}'

    @property
    def bunga_rp(self):
        from decimal import Decimal
        return self.jumlah_rp * self.bunga_persen / Decimal('100')


class PenjualanGabah(models.Model):
    tanggal = models.DateField(verbose_name='Tanggal Penjualan')
    jumlah_kg = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Jumlah (kg)')
    harga_per_100kg = models.DecimalField(
        max_digits=12, decimal_places=2, verbose_name='Harga per 100 kg (Rp)'
    )
    total_rp = models.DecimalField(
        max_digits=15, decimal_places=2, verbose_name='Total (Rp)',
        help_text='Otomatis dihitung: (jumlah_kg / 100) × harga_per_100kg'
    )
    pembeli = models.CharField(max_length=200, verbose_name='Nama Pembeli')
    keterangan = models.TextField(blank=True, verbose_name='Keterangan')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Penjualan Gabah'
        verbose_name_plural = 'Penjualan Gabah'

    def __str__(self):
        return f'{self.pembeli} - {self.jumlah_kg} kg - Rp {self.total_rp:,.0f}'

    def save(self, *args, **kwargs):
        from decimal import Decimal
        self.total_rp = (self.jumlah_kg / Decimal('100')) * self.harga_per_100kg
        super().save(*args, **kwargs)

    # TAMBAHKAN BLOK INI
    @property
    def total_harga(self):
        if self.jumlah_kg and self.harga_per_100kg:
            return (self.jumlah_kg / 100) * self.harga_per_100kg
        return 0


class Pengeluaran(models.Model):
    KATEGORI_CHOICES = [
        ('operasional', 'Operasional'),
        ('gaji', 'Gaji'),
        ('transport', 'Transport'),
        ('peralatan', 'Peralatan'),
        ('lainnya', 'Lainnya'),
    ]
    tanggal = models.DateField(verbose_name='Tanggal')
    kategori = models.CharField(
        max_length=50, choices=KATEGORI_CHOICES, default='operasional', verbose_name='Kategori'
    )
    keterangan = models.CharField(max_length=300, verbose_name='Keterangan')
    jumlah_rp = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Jumlah (Rp)')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Pengeluaran'
        verbose_name_plural = 'Pengeluaran'

    def __str__(self):
        return f'{self.keterangan} - Rp {self.jumlah_rp:,.0f}'
    

class BukuKas(models.Model):
    TIPE_CHOICES = [
        ('masuk', 'Kas Masuk'),
        ('keluar', 'Kas Keluar'),
    ]
    KATEGORI_CHOICES = [
        ('iuran_panen', 'Iuran Panen Gabah'),
        ('penjualan_gabah', 'Penjualan Gabah'),
        ('simpanan_masuk', 'Simpanan Anggota Masuk'),
        ('pinjaman_keluar', 'Pinjaman Anggota Keluar'),
        ('pinjaman_masuk', 'Pengembalian Pinjaman Anggota'),
        ('operasional', 'Biaya Operasional'),
        ('lainnya', 'Lainnya'),
    ]
    
    tanggal = models.DateField(verbose_name='Tanggal Transaksi')
    tipe = models.CharField(max_length=10, choices=TIPE_CHOICES, verbose_name='Tipe Arus Kas')
    kategori = models.CharField(max_length=20, choices=KATEGORI_CHOICES, verbose_name='Kategori')
    jumlah_rp = models.DecimalField(max_digits=15, decimal_places=2, verbose_name='Jumlah (Rp)')
    keterangan = models.TextField(blank=True, verbose_name='Keterangan')
    referensi = models.CharField(max_length=100, blank=True, verbose_name='No. Referensi', help_text='Opsional: No Kwitansi atau ID Transaksi Asal')

    class Meta:
        ordering = ['-tanggal']
        verbose_name = 'Buku Kas'
        verbose_name_plural = 'Buku Kas'

    def __str__(self):
        return f'{self.get_tipe_display()} - {self.kategori} - Rp {self.jumlah_rp:,.0f}'
