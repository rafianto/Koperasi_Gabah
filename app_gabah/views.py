import json
import calendar
from decimal import Decimal
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Sum, Q  # ← WAJIB ADA
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from .models import Anggota, HargaGabah, IuranPanen, SimpanPinjam, PenjualanGabah, Pengeluaran
from .forms import (
    AnggotaForm, HargaGabahForm, IuranPanenForm,
    SimpanPinjamForm, PenjualanGabahForm, PengeluaranForm
)
from .models import Pengeluaran
from .models import PenjualanGabah
from .forms import PenjualanGabahForm


# ===================== AUTH =====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Username atau password salah!')
    return render(request, 'app_gabah/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Berhasil logout.')
    return redirect('login')


# ===================== DASHBOARD =====================

@login_required
def dashboard(request):
    year = int(request.GET.get('year', date.today().year))

    # Ringkasan Anggota
    total_anggota = Anggota.objects.count()
    anggota_aktif = Anggota.objects.filter(status='aktif').count()

    # Ringkasan Gabah
    iuran_kg = IuranPanen.objects.filter(tanggal__year=year).aggregate(
        total=Sum('jumlah_kg'))['total'] or Decimal('0')
    iuran_kg_all = IuranPanen.objects.aggregate(
        total=Sum('jumlah_kg'))['total'] or Decimal('0')
    penjualan_kg = PenjualanGabah.objects.filter(tanggal__year=year).aggregate(
        total=Sum('jumlah_kg'))['total'] or Decimal('0')
    penjualan_kg_all = PenjualanGabah.objects.aggregate(
        total=Sum('jumlah_kg'))['total'] or Decimal('0')
    stok_gabah_kg = iuran_kg_all - penjualan_kg_all

    # Ringkasan Keuangan
    total_simpanan = SimpanPinjam.objects.filter(
        tipe='simpanan', status='aktif').aggregate(total=Sum('jumlah_rp'))['total'] or Decimal('0')
    total_pinjaman = SimpanPinjam.objects.filter(
        tipe='pinjaman', status='aktif').aggregate(total=Sum('jumlah_rp'))['total'] or Decimal('0')
    total_penjualan_rp = PenjualanGabah.objects.filter(
        tanggal__year=year).aggregate(total=Sum('total_rp'))['total'] or Decimal('0')
    total_pengeluaran_rp = Pengeluaran.objects.filter(
        tanggal__year=year).aggregate(total=Sum('jumlah_rp'))['total'] or Decimal('0')

    # Bunga pinjaman (pendapatan)
    bunga_pinjaman = Decimal('0')
    for sp in SimpanPinjam.objects.filter(tipe='pinjaman', tanggal__year=year):
        bunga_pinjaman += sp.bunga_rp

    # Bunga simpanan (beban)
    bunga_simpanan = Decimal('0')
    for sp in SimpanPinjam.objects.filter(tipe='simpanan', tanggal__year=year):
        bunga_simpanan += sp.bunga_rp

    total_pendapatan = total_penjualan_rp + bunga_pinjaman
    total_beban = total_pengeluaran_rp + bunga_simpanan
    laba_rugi = total_pendapatan - total_beban

    # Harga gabah terbaru
    # harga_terbaru = HargaGabah.get_harga_terbaru()
    # Harga gabah terbaru (Mengambil tanggal paling muda/terbaru)
    harga_obj = HargaGabah.objects.order_by('-tanggal').first()
    harga_terbaru = harga_obj.harga_per_100kg if harga_obj else Decimal('0')

    # Data chart bulanan
    chart_labels = [calendar.month_abbr[m] for m in range(1, 13)]
    chart_penjualan = []
    chart_pengeluaran = []
    chart_iuran_kg = []
    chart_penjualan_kg = []

    for m in range(1, 13):
        penj = PenjualanGabah.objects.filter(
            tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('total_rp'))['total'] or 0
        peng = Pengeluaran.objects.filter(
            tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('jumlah_rp'))['total'] or 0
        iur = IuranPanen.objects.filter(
            tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('jumlah_kg'))['total'] or 0
        penjk = PenjualanGabah.objects.filter(
            tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('jumlah_kg'))['total'] or 0
        chart_penjualan.append(float(penj))
        chart_pengeluaran.append(float(peng))
        chart_iuran_kg.append(float(iur))
        chart_penjualan_kg.append(float(penjk))

    # Performa
    efisiensi_penjualan = float(penjualan_kg / iuran_kg * 100) if iuran_kg > 0 else 0
    rasio_pinjaman_simpanan = float(total_pinjaman / total_simpanan * 100) if total_simpanan > 0 else 0
    rata_iuran_per_anggota = float(iuran_kg / anggota_aktif) if anggota_aktif > 0 else 0
    pendapatan_per_kg = float(total_penjualan_rp / penjualan_kg) if penjualan_kg > 0 else 0

    # Transaksi terbaru
    iuran_terbaru = IuranPanen.objects.order_by('-tanggal')[:5]
    penjualan_terbaru = PenjualanGabah.objects.order_by('-tanggal')[:5]

    # Daftar tahun untuk filter
    years = []
    current_year = date.today().year
    for y in range(current_year - 3, current_year + 2):
        years.append(y)

    context = {
        'total_anggota': total_anggota,
        'anggota_aktif': anggota_aktif,
        'iuran_kg': iuran_kg,
        'stok_gabah_kg': stok_gabah_kg,
        'penjualan_kg': penjualan_kg,
        'total_simpanan': total_simpanan,
        'total_pinjaman': total_pinjaman,
        'total_penjualan_rp': total_penjualan_rp,
        'total_pengeluaran_rp': total_pengeluaran_rp,
        'total_pendapatan': total_pendapatan,
        'total_beban': total_beban,
        'laba_rugi': laba_rugi,
        'harga_terbaru': harga_terbaru,
        'bunga_pinjaman': bunga_pinjaman,
        'bunga_simpanan': bunga_simpanan,
        'efisiensi_penjualan': efisiensi_penjualan,
        'rasio_pinjaman_simpanan': rasio_pinjaman_simpanan,
        'rata_iuran_per_anggota': rata_iuran_per_anggota,
        'pendapatan_per_kg': pendapatan_per_kg,
        'iuran_terbaru': iuran_terbaru,
        'penjualan_terbaru': penjualan_terbaru,
        'chart_labels': json.dumps(chart_labels),
        'chart_penjualan': json.dumps(chart_penjualan),
        'chart_pengeluaran': json.dumps(chart_pengeluaran),
        'chart_iuran_kg': json.dumps(chart_iuran_kg),
        'chart_penjualan_kg': json.dumps(chart_penjualan_kg),
        'year': year,
        'years': years,
    }
    return render(request, 'app_gabah/dashboard.html', context)


# ===================== RUGI LABA =====================

@login_required
def rugi_laba(request):
    year = int(request.GET.get('year', date.today().year))
    month = request.GET.get('month')

    iuran_base = IuranPanen.objects.filter(tanggal__year=year)
    penjualan_base = PenjualanGabah.objects.filter(tanggal__year=year)
    pengeluaran_base = Pengeluaran.objects.filter(tanggal__year=year)
    sp_pinjaman_base = SimpanPinjam.objects.filter(tipe='pinjaman', tanggal__year=year)
    sp_simpanan_base = SimpanPinjam.objects.filter(tipe='simpanan', tanggal__year=year)

    if month:
        month = int(month)
        iuran_base = iuran_base.filter(tanggal__month=month)
        penjualan_base = penjualan_base.filter(tanggal__month=month)
        pengeluaran_base = pengeluaran_base.filter(tanggal__month=month)
        sp_pinjaman_base = sp_pinjaman_base.filter(tanggal__month=month)
        sp_simpanan_base = sp_simpanan_base.filter(tanggal__month=month)

    total_penjualan = penjualan_base.aggregate(total=Sum('total_rp'))['total'] or Decimal('0')
    total_pengeluaran = pengeluaran_base.aggregate(total=Sum('jumlah_rp'))['total'] or Decimal('0')
    total_iuran_nilai = iuran_base.aggregate(total=Sum('nilai_rp'))['total'] or Decimal('0')
    total_iuran_kg = iuran_base.aggregate(total=Sum('jumlah_kg'))['total'] or Decimal('0')

    bunga_pinjaman = sum((sp.bunga_rp for sp in sp_pinjaman_base), Decimal('0'))
    bunga_simpanan = sum((sp.bunga_rp for sp in sp_simpanan_base), Decimal('0'))

    total_pendapatan = total_penjualan + bunga_pinjaman
    total_beban = total_pengeluaran + bunga_simpanan
    laba_rugi = total_pendapatan - total_beban

    # Pengeluaran per kategori
    peng_per_kategori = {}
    for kat_key, kat_label in Pengeluaran.KATEGORI_CHOICES:
        val = pengeluaran_base.filter(kategori=kat_key).aggregate(
            total=Sum('jumlah_rp'))['total'] or 0
        if val > 0:
            peng_per_kategori[kat_label] = float(val)

    # Chart data bulanan
    chart_labels = [calendar.month_abbr[m] for m in range(1, 13)]
    chart_pendapatan = []
    chart_beban = []
    for m in range(1, 13):
        p = PenjualanGabah.objects.filter(tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('total_rp'))['total'] or 0
        bp = sum((sp.bunga_rp for sp in SimpanPinjam.objects.filter(
            tipe='pinjaman', tanggal__year=year, tanggal__month=m)), Decimal('0'))
        chart_pendapatan.append(float(p + bp))

        b = Pengeluaran.objects.filter(tanggal__year=year, tanggal__month=m).aggregate(
            total=Sum('jumlah_rp'))['total'] or 0
        bs = sum((sp.bunga_rp for sp in SimpanPinjam.objects.filter(
            tipe='simpanan', tanggal__year=year, tanggal__month=m)), Decimal('0'))
        chart_beban.append(float(b + bs))

    context = {
        'year': year,
        'month': month,
        'total_penjualan': total_penjualan,
        'total_iuran_nilai': total_iuran_nilai,
        'total_iuran_kg': total_iuran_kg,
        'bunga_pinjaman': bunga_pinjaman,
        'total_pendapatan': total_pendapatan,
        'total_pengeluaran': total_pengeluaran,
        'bunga_simpanan': bunga_simpanan,
        'total_beban': total_beban,
        'laba_rugi': laba_rugi,
        'peng_per_kategori': peng_per_kategori,
        'chart_labels': json.dumps(chart_labels),
        'chart_pendapatan': json.dumps(chart_pendapatan),
        'chart_beban': json.dumps(chart_beban),
    }
    return render(request, 'app_gabah/rugilaba.html', context)


# ===================== ANGGOTA CRUD =====================

@login_required
def anggota_list(request):
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    queryset = Anggota.objects.all()
    if search:
        queryset = queryset.filter(Q(nama__icontains=search) | Q(nik__icontains=search))
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    queryset = queryset.order_by('nama')
    context = {'object_list': queryset, 'search': search, 'status_filter': status_filter}
    return render(request, 'app_gabah/anggota_list.html', context)


@login_required
def anggota_create(request):
    if request.method == 'POST':
        form = AnggotaForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Anggota berhasil ditambahkan!')
            return redirect('anggota_list')
    else:
        form = AnggotaForm()
    return render(request, 'app_gabah/anggota_form.html', {'form': form, 'title': 'Tambah Anggota'})


@login_required
def anggota_update(request, pk):
    obj = get_object_or_404(Anggota, pk=pk)
    if request.method == 'POST':
        form = AnggotaForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data anggota berhasil diperbarui!')
            return redirect('anggota_list')
    else:
        form = AnggotaForm(instance=obj)
    return render(request, 'app_gabah/anggota_form.html', {'form': form, 'title': 'Edit Anggota'})

@login_required
def anggota_detail(request, pk):
    anggota = get_object_or_404(Anggota, pk=pk)
    return render(request, 'app_gabah/anggota_detail.html', {
        'anggota': anggota,
        'iuran': anggota.iuranpanen_set.order_by('-tanggal'),
        'simp': anggota.simpanpinjam_set.filter(tipe='simpanan').order_by('-tanggal'),
        'pinj': anggota.simpanpinjam_set.filter(tipe='pinjaman').order_by('-tanggal'),
    })

@login_required
def anggota_delete(request, pk):
    anggota = get_object_or_404(Anggota, pk=pk)
    if request.method == 'POST':
        anggota.delete()
        messages.success(request, f'Anggota "{anggota.nama}" berhasil dihapus!')
        return redirect('anggota_list')
    return render(request, 'app_gabah/anggota_confirm_delete.html', {'anggota': anggota})



# ==================== IURAN CRUD ====================
@login_required
def iuran_list(request):
    af = request.GET.get('af', '')
    pf = request.GET.get('pf', '')
    qs = IuranPanen.objects.select_related('anggota').all()
    if af:
        qs = qs.filter(anggota_id=af)
    if pf:
        qs = qs.filter(periode__icontains=pf)
    qs = qs.order_by('-tanggal')
    return render(request, 'app_gabah/iuran_list.html', {
        'object_list': qs,
        'anggota_list': Anggota.objects.filter(status='aktif'),
        'af': af,
        'pf': pf,
        'tkg': qs.aggregate(t=Sum('jumlah_kg'))['t'] or 0,
        'trp': qs.aggregate(t=Sum('nilai_rp'))['t'] or 0,
    })

@login_required
def iuran_create(request):
    if request.method == 'POST':
        form = IuranPanenForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Iuran panen berhasil dicatat!')
            return redirect('iuran_list')
    else:
        form = IuranPanenForm()
    return render(request, 'app_gabah/iuran_form.html', {'form': form, 'title': 'Tambah Iuran Panen'})

@login_required
def iuran_update(request, pk):
    obj = get_object_or_404(IuranPanen, pk=pk)
    if request.method == 'POST':
        form = IuranPanenForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Iuran panen berhasil diperbarui!')
            return redirect('iuran_list')
    else:
        form = IuranPanenForm(instance=obj)
    return render(request, 'app_gabah/iuran_form.html', {'form': form, 'title': 'Edit Iuran Panen'})

@login_required
def iuran_delete(request, pk):
    iuran = get_object_or_404(IuranPanen, pk=pk)
    if request.method == 'POST':
        iuran.delete()
        messages.success(request, 'Data iuran panen berhasil dihapus!')
        return redirect('iuran_list')
    return render(request, 'app_gabah/iuran_confirm_delete.html', {'iuran': iuran})


# ===================== SIMPAN PINJAM CRUD =====================
# ==================== SIMPAN PINJAM CRUD ====================
@login_required
def sp_list(request):
    tf = request.GET.get('tf', '')
    sf = request.GET.get('sf', '')
    af = request.GET.get('af', '')
    qs = SimpanPinjam.objects.select_related('anggota').all()
    if tf:
        qs = qs.filter(tipe=tf)
    if sf:
        qs = qs.filter(status=sf)
    if af:
        qs = qs.filter(anggota_id=af)
    qs = qs.order_by('-tanggal')
    ts = qs.filter(tipe='simpanan').aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')
    tp = qs.filter(tipe='pinjaman').aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')
    return render(request, 'app_gabah/simpanpinjam_list.html', {
        'object_list': qs,
        'anggota_list': Anggota.objects.filter(status='aktif'),
        'tf': tf, 'sf': sf, 'af': af, 'ts': ts, 'tp': tp,
    })

@login_required
def sp_create(request):
    if request.method == 'POST':
        form = SimpanPinjamForm(request.POST)
        if form.is_valid():
            try:
                obj = form.save()
                tipe_name = obj.get_tipe_display()
                messages.success(request, f'Data {tipe_name} berhasil dicatat!')
                return redirect('sp_list')
            except Exception as e:
                messages.error(request, f'Gagal menyimpan: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f'{field}: {err}')
    else:
        form = SimpanPinjamForm()
        # Default status aktif saat create
        form.initial['status'] = 'aktif'
    return render(request, 'app_gabah/simpanpinjam_form.html', {'form': form, 'title': 'Tambah Simpanan/Pinjaman'})

@login_required
def sp_update(request, pk):
    obj = get_object_or_404(SimpanPinjam, pk=pk)
    if request.method == 'POST':
        form = SimpanPinjamForm(request.POST, instance=obj)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Data berhasil diperbarui!')
                return redirect('sp_list')
            except Exception as e:
                messages.error(request, f'Gagal menyimpan: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f'{field}: {err}')
    else:
        form = SimpanPinjamForm(instance=obj)
    return render(request, 'app_gabah/simpanpinjam_form.html', {'form': form, 'title': 'Edit Simpanan/Pinjaman', 'obj': obj})

@login_required
def sp_lunasi(request, pk):
    obj = get_object_or_404(SimpanPinjam, pk=pk, tipe='pinjaman', status='aktif')
    obj.status = 'lunas'
    obj.save()
    messages.success(request, f'Pinjaman {obj.anggota.nama} sebesar Rp {obj.jumlah_rp|floatformat:0} berhasil dilunasi!')
    return redirect('sp_list')

@login_required
def sp_delete(request, pk):
    sp = get_object_or_404(SimpanPinjam, pk=pk)
    if request.method == 'POST':
        tipe_name = sp.get_tipe_display()
        sp.delete()
        messages.success(request, f'Data {tipe_name} berhasil dihapus!')
        return redirect('sp_list')
    return render(request, 'app_gabah/simpanpinjam_confirm_delete.html', {'sp': sp})

# ===================== PENJUALAN GABAH CRUD =====================

@login_required
def penjualan_list(request):
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    queryset = PenjualanGabah.objects.all()
    if date_from:
        queryset = queryset.filter(tanggal__gte=date_from)
    if date_to:
        queryset = queryset.filter(tanggal__lte=date_to)
    queryset = queryset.order_by('-tanggal')
    total_kg = queryset.aggregate(total=Sum('jumlah_kg'))['total'] or 0
    total_rp = queryset.aggregate(total=Sum('total_rp'))['total'] or 0
    context = {
        'object_list': queryset,
        'date_from': date_from,
        'date_to': date_to,
        'total_kg': total_kg,
        'total_rp': total_rp,
    }
    return render(request, 'app_gabah/penjualan_list.html', context)


@login_required
def penjualan_create(request):
    if request.method == 'POST':
        form = PenjualanGabahForm(request.POST)
        if form.is_valid():
            # Validasi stok
            stok = IuranPanen.objects.aggregate(total=Sum('jumlah_kg'))['total'] or Decimal('0')
            stok -= PenjualanGabah.objects.aggregate(total=Sum('jumlah_kg'))['total'] or Decimal('0')
            if form.cleaned_data['jumlah_kg'] > stok:
                messages.error(request, f'Stok gabah tidak mencukupi! Sisa stok: {stok} kg')
                return render(request, 'app_gabah/penjualan_form.html', {'form': form, 'title': 'Tambah Penjualan'})
            form.save()
            messages.success(request, 'Penjualan gabah berhasil dicatat!')
            return redirect('penjualan_list')
    else:
        form = PenjualanGabahForm()
    return render(request, 'app_gabah/penjualan_form.html', {'form': form, 'title': 'Tambah Penjualan Gabah'})


@login_required
def penjualan_update(request, pk):
    obj = get_object_or_404(PenjualanGabah, pk=pk)
    if request.method == 'POST':
        form = PenjualanGabahForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Data penjualan berhasil diperbarui!')
            return redirect('penjualan_list')
    else:
        form = PenjualanGabahForm(instance=obj)
    return render(request, 'app_gabah/penjualan_form.html', {'form': form, 'title': 'Edit Penjualan Gabah'})


@login_required
def penjualan_delete(request, pk):
    penjualan = get_object_or_404(PenjualanGabah, pk=pk)
    if request.method == 'POST':
        penjualan.delete()
        messages.success(request, 'Data penjualan berhasil dihapus!')
        return redirect('penjualan_list')
    
    # PASTIKAN MENGGUNAKAN 'object'=penjualan
    return render(request, 'app_gabah/penjualan_confirm_delete.html', {
        'object': penjualan
    })


# ===================== HARGA GABAH CRUD =====================

@login_required
def harga_list(request):
    queryset = HargaGabah.objects.all()
    context = {'object_list': queryset}
    return render(request, 'app_gabah/harga_list.html', context)


@login_required
def harga_create(request):
    if request.method == 'POST':
        form = HargaGabahForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Harga gabah berhasil ditambahkan!')
            return redirect('harga_list')
    else:
        form = HargaGabahForm()
    return render(request, 'app_gabah/harga_form.html', {'form': form, 'title': 'Tambah Harga Gabah'})


@login_required
def harga_update(request, pk):
    obj = get_object_or_404(HargaGabah, pk=pk)
    if request.method == 'POST':
        form = HargaGabahForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Harga gabah berhasil diperbarui!')
            return redirect('harga_list')
    else:
        form = HargaGabahForm(instance=obj)
    return render(request, 'app_gabah/harga_form.html', {'form': form, 'title': 'Edit Harga Gabah'})


@login_required
def harga_delete(request, pk):
    harga = get_object_or_404(HargaGabah, pk=pk)
    if request.method == 'POST':
        harga.delete()
        messages.success(request, 'Harga gabah berhasil dihapus!')
        return redirect('harga_list')
    return render(request, 'app_gabah/harga_confirm_delete.html', {'harga': harga})


# ===================== PENGELUARAN CRUD =====================

@login_required
@login_required
def pengeluaran_list(request):
    queryset = Pengeluaran.objects.all()

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(keterangan__icontains=search) |
            Q(kategori__icontains=search)
        )

    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        queryset = queryset.filter(kategori=kategori_filter)

    tanggal_dari = request.GET.get('tanggal_dari', '')
    tanggal_sampai = request.GET.get('tanggal_sampai', '')
    if tanggal_dari:
        queryset = queryset.filter(tanggal__gte=tanggal_dari)
    if tanggal_sampai:
        queryset = queryset.filter(tanggal__lte=tanggal_sampai)

    queryset = queryset.order_by('-tanggal')
    total_pengeluaran = queryset.aggregate(total=Sum('jumlah_rp')).get('total') or 0

    return render(request, 'app_gabah/pengeluaran_list.html', {
        'object_list': queryset,
        'search': search,
        'kategori_filter': kategori_filter,
        'tanggal_dari': tanggal_dari,
        'tanggal_sampai': tanggal_sampai,
        'total_pengeluaran': total_pengeluaran,
    })


@login_required
def pengeluaran_create(request):
    if request.method == 'POST':
        form = PengeluaranForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pengeluaran berhasil dicatat!')
            return redirect('pengeluaran_list')
    else:
        form = PengeluaranForm()
    return render(request, 'app_gabah/pengeluaran_form.html', {'form': form, 'title': 'Tambah Pengeluaran'})


@login_required
def pengeluaran_update(request, pk):
    obj = get_object_or_404(Pengeluaran, pk=pk)
    if request.method == 'POST':
        form = PengeluaranForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Pengeluaran berhasil diperbarui!')
            return redirect('pengeluaran_list')
    else:
        form = PengeluaranForm(instance=obj)
    return render(request, 'app_gabah/pengeluaran_form.html', {'form': form, 'title': 'Edit Pengeluaran'})


@login_required
def pengeluaran_delete(request, pk):
    obj = get_object_or_404(Pengeluaran, pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, 'Pengeluaran berhasil dihapus!')
        return redirect('pengeluaran_list')
    return render(request, 'app_gabah/pengeluran_confirm_delete.html', {
        'object': obj, 'cancel_url': 'pengeluaran_list', 'title': 'Hapus Pengeluaran'
    })

@login_required
def rugi_laba(request):
    
    year = int(request.GET.get('year', date.today().year))
    month = request.GET.get('month')
    
    pb = PenjualanGabah.objects.filter(tanggal__year=year)
    pgb = Pengeluaran.objects.filter(tanggal__year=year)
    ib = IuranPanen.objects.filter(tanggal__year=year)
    spb = SimpanPinjam.objects.filter(tipe='pinjaman', tanggal__year=year)
    ssb = SimpanPinjam.objects.filter(tipe='simpanan', tanggal__year=year)

    if month:
        m = int(month)
        pb = pb.filter(tanggal__month=m)
        pgb = pgb.filter(tanggal__month=m)
        ib = ib.filter(tanggal__month=m)
        spb = spb.filter(tanggal__month=m)
        ssb = ssb.filter(tanggal__month=m)

    total_penjualan = pb.aggregate(t=Sum('total_rp'))['t'] or Decimal('0')
    total_pengeluaran = pgb.aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')
    total_iuran_nilai = ib.aggregate(t=Sum('nilai_rp'))['t'] or Decimal('0')
    total_iuran_kg = ib.aggregate(t=Sum('jumlah_kg'))['t'] or Decimal('0')
    bunga_pinjaman = sum((sp.bunga_rp for sp in spb), Decimal('0'))
    bunga_simpanan = sum((sp.bunga_rp for sp in ssb), Decimal('0'))
    total_pendapatan = total_penjualan + bunga_pinjaman
    total_beban = total_pengeluaran + bunga_simpanan
    laba_rugi = total_pendapatan - total_beban

    peng_per_kategori = {}
    for kat_key, kat_label in Pengeluaran.KATEGORI_CHOICES:
        val = pgb.filter(kategori=kat_key).aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')
        if val > 0:
            peng_per_kategori[kat_label] = float(val)

    chart_labels = [calendar.month_abbr[m] for m in range(1, 13)]
    chart_pendapatan, chart_beban = [], []
    for m in range(1, 13):
        p = float(PenjualanGabah.objects.filter(tanggal__year=year, tanggal__month=m).aggregate(t=Sum('total_rp'))['t'] or 0)
        bp = float(sum((sp.bunga_rp for sp in SimpanPinjam.objects.filter(tipe='pinjaman', tanggal__year=year, tanggal__month=m)), Decimal('0')))
        chart_pendapatan.append(p + bp)
        b = float(Pengeluaran.objects.filter(tanggal__year=year, tanggal__month=m).aggregate(t=Sum('jumlah_rp'))['t'] or 0)
        bs = float(sum((sp.bunga_rp for sp in SimpanPinjam.objects.filter(tipe='simpanan', tanggal__year=year, tanggal__month=m)), Decimal('0')))
        chart_beban.append(b + bs)

    # ===== FIX: Convert dict keys/values to JSON string =====
    kat_labels_json = json.dumps(list(peng_per_kategori.keys()))
    kat_values_json = json.dumps(list(peng_per_kategori.values()))

    context = {
        'year': year, 'month': month,
        'total_penjualan': total_penjualan, 'total_pengeluaran': total_pengeluaran,
        'total_iuran_nilai': total_iuran_nilai, 'total_iuran_kg': total_iuran_kg,
        'bunga_pinjaman': bunga_pinjaman, 'bunga_simpanan': bunga_simpanan,
        'total_pendapatan': total_pendapatan, 'total_beban': total_beban,
        'laba_rugi': laba_rugi, 'peng_per_kategori': peng_per_kategori,
        'chart_labels': json.dumps(chart_labels), 'chart_pendapatan': json.dumps(chart_pendapatan),
        'chart_beban': json.dumps(chart_beban),
        'kat_labels_json': kat_labels_json, 'kat_values_json': kat_values_json,
    }
    return render(request, 'app_gabah/rugilaba.html', context)

def pengeluaran_list(request):
    from django.db.models import Sum, Q

    queryset = Pengeluaran.objects.all()

    search = request.GET.get('search', '')
    if search:
        queryset = queryset.filter(
            Q(keterangan__icontains=search) |
            Q(kategori__icontains=search)
        )

    kategori_filter = request.GET.get('kategori', '')
    if kategori_filter:
        queryset = queryset.filter(kategori=kategori_filter)

    tanggal_dari = request.GET.get('tanggal_dari', '')
    tanggal_sampai = request.GET.get('tanggal_sampai', '')
    if tanggal_dari:
        queryset = queryset.filter(tanggal__gte=tanggal_dari)
    if tanggal_sampai:
        queryset = queryset.filter(tanggal__lte=tanggal_sampai)

    # PERHATIKAN BAGIAN RETURN DI BAWAH!
    return render(request, 'app_gabah/pengeluaran_list.html', {
        'object_list': queryset,
        'search': search,
        'kategori_filter': kategori_filter,
        'tanggal_dari': tanggal_dari,
        'tanggal_sampai': tanggal_sampai,
        'total_pengeluaran': queryset.aggregate(total=Sum('jumlah_rp')).get('total') or 0,  # ← GUNAKAN : DAN jumlah_rp
    })