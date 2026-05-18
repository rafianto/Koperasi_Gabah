# app_gabah/forms.py

from django import forms
from .models import Anggota, HargaGabah, IuranPanen, SimpanPinjam, PenjualanGabah, Pengeluaran

class AnggotaForm(forms.ModelForm):
    class Meta:
        model = Anggota
        fields = ['nama', 'nik', 'alamat', 'telepon', 'status']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'fi', 'placeholder': 'Nama lengkap'}),
            'nik': forms.TextInput(attrs={'class': 'fi', 'placeholder': 'NIK'}),
            'alamat': forms.Textarea(attrs={'class': 'fi', 'rows': 3}),
            'telepon': forms.TextInput(attrs={'class': 'fi', 'placeholder': '08xx'}),
            'status': forms.Select(attrs={'class': 'fi'}),
        }


class HargaGabahForm(forms.ModelForm):
    class Meta:
        model = HargaGabah
        fields = ['tanggal', 'harga_per_100kg', 'catatan']
        widgets = {
            'tanggal': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'harga_per_100kg': forms.NumberInput(attrs={'class': 'fi'}),
            'catatan': forms.Textarea(attrs={'class': 'fi', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tanggal:
            self.initial['tanggal'] = self.instance.tanggal.strftime('%Y-%m-%d')


class IuranPanenForm(forms.ModelForm):
    class Meta:
        model = IuranPanen
        fields = ['anggota', 'periode', 'jumlah_kg', 'tanggal', 'harga_per_100kg', 'keterangan']
        widgets = {
            'anggota': forms.Select(attrs={'class': 'fi'}),
            'periode': forms.TextInput(attrs={'class': 'fi', 'placeholder': 'Januari 2024'}),
            'jumlah_kg': forms.NumberInput(attrs={'class': 'fi', 'placeholder': '150', 'step': '0.1', 'min': '0'}),
            'tanggal': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'harga_per_100kg': forms.NumberInput(attrs={'class': 'fi', 'placeholder': '500000', 'min': '0'}),
            'keterangan': forms.Textarea(attrs={'class': 'fi', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tanggal:
            self.initial['tanggal'] = self.instance.tanggal.strftime('%Y-%m-%d')
        if not self.instance.pk:
            try:
                harga = HargaGabah.objects.first()
                if harga:
                    self.initial['harga_per_100kg'] = harga.harga_per_100kg
            except:
                pass

    def clean_jumlah_kg(self):
        value = self.cleaned_data.get('jumlah_kg')
        if value is not None and value <= 0:
            raise forms.ValidationError('Jumlah kg harus lebih dari 0')
        return value

    def clean_harga_per_100kg(self):
        value = self.cleaned_data.get('harga_per_100kg')
        if value is not None and value <= 0:
            raise forms.ValidationError('Harga harus lebih dari 0')
        return value


class SimpanPinjamForm(forms.ModelForm):
    class Meta:
        model = SimpanPinjam
        fields = ['anggota', 'tipe', 'jumlah_rp', 'bunga_persen', 'tanggal', 'jatuh_tempo', 'keterangan', 'status']
        widgets = {
            'anggota': forms.Select(attrs={'class': 'fi'}),
            'tipe': forms.Select(attrs={'class': 'fi'}),
            'jumlah_rp': forms.NumberInput(attrs={'class': 'fi', 'placeholder': 'Jumlah dalam Rupiah'}),
            'bunga_persen': forms.NumberInput(attrs={'class': 'fi', 'placeholder': '0 jika tanpa bunga', 'step': '0.1'}),
            'tanggal': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'jatuh_tempo': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'keterangan': forms.Textarea(attrs={'class': 'fi', 'rows': 2, 'placeholder': 'Keterangan'}),
            'status': forms.Select(attrs={'class': 'fi'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.tanggal:
                self.initial['tanggal'] = self.instance.tanggal.strftime('%Y-%m-%d')
            if self.instance.jatuh_tempo:
                self.initial['jatuh_tempo'] = self.instance.jatuh_tempo.strftime('%Y-%m-%d')
        if not self.instance.pk:
            self.initial['status'] = 'aktif'


class PenjualanGabahForm(forms.ModelForm):
    class Meta:
        model = PenjualanGabah
        fields = ['tanggal', 'jumlah_kg', 'harga_per_100kg', 'pembeli', 'keterangan']
        widgets = {
            'tanggal': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'jumlah_kg': forms.NumberInput(attrs={'class': 'fi', 'placeholder': 'Jumlah dalam kg'}),
            'harga_per_100kg': forms.NumberInput(attrs={'class': 'fi', 'placeholder': 'Harga per 100 kg'}),
            'pembeli': forms.TextInput(attrs={'class': 'fi', 'placeholder': 'Nama pembeli'}),
            'keterangan': forms.Textarea(attrs={'class': 'fi', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.tanggal:
            self.initial['tanggal'] = self.instance.tanggal.strftime('%Y-%m-%d')
        if not self.instance.pk:
            try:
                harga = HargaGabah.objects.first()
                if harga:
                    self.initial['harga_per_100kg'] = harga.harga_per_100kg
            except:
                pass


# ================= PERBAIKAN DI SINI =================
# GANTI class Pengeluaran(models.Model) MENJADI class PengeluaranForm(forms.ModelForm)

class PengeluaranForm(forms.ModelForm):
    class Meta:
        model = Pengeluaran  # Mengarah ke model Pengeluaran yang ada di models.py
        fields = ['tanggal', 'kategori', 'keterangan', 'jumlah_rp']
        widgets = {
            'tanggal': forms.DateInput(attrs={'class': 'fi', 'type': 'date'}, format='%Y-%m-%d'),
            'kategori': forms.Select(attrs={'class': 'fi'}),
            'keterangan': forms.TextInput(attrs={'class': 'fi', 'placeholder': 'Misal: Beli bensin operasional'}),
            'jumlah_rp': forms.NumberInput(attrs={'class': 'fi', 'step': '1000', 'placeholder': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fix format tanggal saat edit (sama seperti form lainnya)
        if self.instance and self.instance.pk and self.instance.tanggal:
            self.initial['tanggal'] = self.instance.tanggal.strftime('%Y-%m-%d')