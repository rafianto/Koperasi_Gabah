from django.urls import path
from . import views

def anggota_pdf_view(request, pk):
    """Lazy import: hanya load views_pdf saat URL diakses."""
    from .views_pdf import anggota_pdf
    return anggota_pdf(request, pk)

urlpatterns = [
    # Auth
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Rugi Laba
    path('rugi-laba/', views.rugi_laba, name='rugi_laba'),
    path('laporan/cashflow/', views.cashflow_view, name='cashflow_report'),

    # Anggota
    path('anggota/', views.anggota_list, name='anggota_list'),
    path('anggota/tambah/', views.anggota_create, name='anggota_create'),
    path('anggota/<int:pk>/edit/', views.anggota_update, name='anggota_update'),
    path('anggota/<int:pk>/', views.anggota_detail, name='anggota_detail'),
    path('anggota/<int:pk>/hapus/', views.anggota_delete, name='anggota_delete'),
    path('anggota/<int:pk>/pdf/', anggota_pdf_view, name='anggota_pdf'),

    # Iuran Panen
    path('iuran/', views.iuran_list, name='iuran_list'),
    path('iuran/tambah/', views.iuran_create, name='iuran_create'),
    path('iuran/<int:pk>/edit/', views.iuran_update, name='iuran_update'),
    path('iuran/<int:pk>/hapus/', views.iuran_delete, name='iuran_delete'),

    # Simpan Pinjam (nama pendek: sp_*)
    path('simpan-pinjam/', views.sp_list, name='sp_list'),
    path('simpan-pinjam/tambah/', views.sp_create, name='sp_create'),
    path('simpan-pinjam/<int:pk>/edit/', views.sp_update, name='sp_update'),
    path('simpan-pinjam/<int:pk>/lunasi/', views.sp_lunasi, name='sp_lunasi'),
    path('simpan-pinjam/<int:pk>/hapus/', views.sp_delete, name='sp_delete'),

    # Penjualan Gabah
    path('penjualan/', views.penjualan_list, name='penjualan_list'),
    path('penjualan/create/', views.penjualan_create, name='penjualan_create'),
    path('penjualan/update/<int:pk>/', views.penjualan_update, name='penjualan_update'),
    path('penjualan/delete/<int:pk>/', views.penjualan_delete, name='penjualan_delete'),

    # Harga Gabah
    path('harga/', views.harga_list, name='harga_list'),
    path('harga/tambah/', views.harga_create, name='harga_create'),
    path('harga/<int:pk>/edit/', views.harga_update, name='harga_update'),
    path('harga/<int:pk>/hapus/', views.harga_delete, name='harga_delete'),

    # Pengeluaran
    path('pengeluaran/', views.pengeluaran_list, name='pengeluaran_list'),
    path('pengeluaran/create/', views.pengeluaran_create, name='pengeluaran_create'),
    path('pengeluaran/update/<int:pk>/', views.pengeluaran_update, name='pengeluaran_update'),
    path('pengeluaran/delete/<int:pk>/', views.pengeluaran_delete, name='pengeluaran_delete'),
]
