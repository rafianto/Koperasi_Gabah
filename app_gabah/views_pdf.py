# =============================================================
# views_pdf.py — Laporan PDF Per Anggota (VERSI LENGKAP)
# Tempatkan: app_gabah/views_pdf.py
# =============================================================

import os
import traceback
from datetime import datetime
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.db.models import Sum

from .models import Anggota, IuranPanen, SimpanPinjam


# =============================================================
# KOP SURAT — SESUAIKAN DENGAN KOPERASI ANDA
# =============================================================
KOP_NAMA = 'KOPERASI GABAH MANDIRI BERSAMA'
KOP_ALAMAT = 'Desa Madureso RT 01 / RW 01 , Kecamatan Kuwarasan, Kabupaten Kebumen'
KOP_TELEPON = 'Telp. (+62) 888-800-7288 | Email: info@koperasigabahsejahtera.id'
# =============================================================


def fmt_rp(val):
    if val is None:
        return 'Rp 0'
    return f'Rp {float(val):,.0f}'.replace(',', '.')


def fmt_kg(val):
    if val is None:
        return '0'
    return f'{float(val):,.1f}'.replace(',', '.')


def fmt_date(val):
    if val is None:
        return '-'
    bulan = {
        1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
        5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
        9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember',
    }
    return f'{val.day} {bulan.get(val.month, "")} {val.year}'


def anggota_pdf(request, pk):
    """Generate laporan PDF per anggota."""

    # ====== LAZY IMPORT ======
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm, cm
        from reportlab.lib.enums import TA_CENTER, TA_RIGHT
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        )
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
    except ImportError:
        return HttpResponse(
            '<html><body style="font-family:Arial; padding:60px; text-align:center;">'
            '<h2 style="color:#dc2626;">ReportLab belum terinstall di venv!</h2>'
            '<p style="font-size:16px; color:#64748b;">Jalankan:</p>'
            '<pre style="background:#f1f5f9; padding:16px; border-radius:8px; '
            'display:inline-block; font-size:18px; color:#059669;">'
            'kopvenv\\Scripts\\python.exe -m pip install reportlab</pre>'
            '</body></html>',
            content_type='text/html', status=500,
        )

    # ====== TRY — error handling ======
    try:
        # ---- Register Fonts ----
        FONT = 'Helvetica'
        FONT_BOLD = 'Helvetica-Bold'

        font_dir = r'C:\Windows\Fonts'
        font_files = {
            'LibSans': 'LiberationSans-Regular.ttf',
            'LibSans-Bold': 'LiberationSans-Bold.ttf',
            'LibSans-Italic': 'LiberationSans-Italic.ttf',
            'LibSans-BoldItalic': 'LiberationSans-BoldItalic.ttf',
        }
        all_exist = all(os.path.exists(os.path.join(font_dir, f)) for f in font_files.values())
        if all_exist:
            try:
                for name, filename in font_files.items():
                    pdfmetrics.registerFont(TTFont(name, os.path.join(font_dir, filename)))
                pdfmetrics.registerFontFamily(
                    'LibSans', normal='LibSans', bold='LibSans-Bold',
                    italic='LibSans-Italic', boldItalic='LibSans-BoldItalic',
                )
                FONT = 'LibSans'
                FONT_BOLD = 'LibSans-Bold'
            except Exception:
                pass  # Fallback ke Helvetica

        # ---- Styles ----
        styles = getSampleStyleSheet()

        S = lambda name, **kw: styles.add(ParagraphStyle(name, **kw))

        S('KopNama', fontName=FONT_BOLD, fontSize=16, leading=20,
          alignment=TA_CENTER, textColor=colors.HexColor('#1e293b'))
        S('KopAlamat', fontName=FONT, fontSize=9, leading=12,
          alignment=TA_CENTER, textColor=colors.HexColor('#64748b'))
        S('JudulLaporan', fontName=FONT_BOLD, fontSize=13, leading=16,
          alignment=TA_CENTER, textColor=colors.HexColor('#0f172a'), spaceAfter=4)
        S('SubJudul', fontName=FONT, fontSize=9, leading=12,
          alignment=TA_CENTER, textColor=colors.HexColor('#64748b'), spaceAfter=12)
        S('SectionTitle', fontName=FONT_BOLD, fontSize=11, leading=14,
          textColor=colors.HexColor('#059669'), spaceBefore=14, spaceAfter=6)
        S('InfoLabel', fontName=FONT, fontSize=9, leading=12,
          textColor=colors.HexColor('#64748b'))
        S('InfoValue', fontName=FONT_BOLD, fontSize=9, leading=12,
          textColor=colors.HexColor('#0f172a'))
        S('TC', fontName=FONT, fontSize=8, leading=10)
        S('TCB', fontName=FONT_BOLD, fontSize=8, leading=10)
        S('Footer', fontName=FONT, fontSize=8, leading=10,
          textColor=colors.HexColor('#94a3b8'), alignment=TA_CENTER)
        S('TtdNama', fontName=FONT_BOLD, fontSize=10, leading=13,
          alignment=TA_CENTER, textColor=colors.HexColor('#0f172a'))
        S('TtdJabatan', fontName=FONT, fontSize=8, leading=11,
          alignment=TA_CENTER, textColor=colors.HexColor('#64748b'))

        tc = styles['TC']
        tcb = styles['TCB']
        white = colors.white

        def hc(text):
            return Paragraph(text, ParagraphStyle('_hc', parent=tc, alignment=TA_CENTER, textColor=white))

        def hr(text):
            return Paragraph(text, ParagraphStyle('_hr', parent=tc, alignment=TA_RIGHT, textColor=white))

        def c(text):
            return Paragraph(text, ParagraphStyle('_c', parent=tc, alignment=TA_CENTER))

        def r(text):
            return Paragraph(text, ParagraphStyle('_r', parent=tc, alignment=TA_RIGHT))

        def rb(text):
            return Paragraph(text, ParagraphStyle('_rb', parent=tcb, alignment=TA_RIGHT))

        def empty_style():
            return ParagraphStyle('_empty', parent=styles['InfoLabel'], alignment=TA_CENTER, spaceBefore=8, spaceAfter=8)

        # ---- Query Data ----
        anggota = get_object_or_404(Anggota, pk=pk)
        iuran_qs = IuranPanen.objects.filter(anggota=anggota).order_by('-tanggal')
        simpanan_qs = SimpanPinjam.objects.filter(anggota=anggota, tipe='simpanan').order_by('-tanggal')
        pinjaman_qs = SimpanPinjam.objects.filter(anggota=anggota, tipe='pinjaman').order_by('-tanggal')

        total_iuran_kg = iuran_qs.aggregate(t=Sum('jumlah_kg'))['t'] or Decimal('0')
        total_iuran_rp = iuran_qs.aggregate(t=Sum('nilai_rp'))['t'] or Decimal('0')
        total_simpanan = simpanan_qs.filter(status='aktif').aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')
        total_pinjaman = pinjaman_qs.filter(status='aktif').aggregate(t=Sum('jumlah_rp'))['t'] or Decimal('0')

        # ---- Build PDF ----
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=1.5*cm, bottomMargin=1.5*cm)
        story = []

        # ====== KOP SURAT ======
        story.append(Paragraph(KOP_NAMA, styles['KopNama']))
        story.append(Paragraph(KOP_ALAMAT, styles['KopAlamat']))
        story.append(Paragraph(KOP_TELEPON, styles['KopAlamat']))
        story.append(Spacer(1, 4*mm))
        story.append(HRFlowable(width='100%', thickness=2, color=colors.HexColor('#059669'), spaceAfter=2*mm))
        story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#059669'), spaceAfter=6*mm))

        # ====== JUDUL ======
        story.append(Paragraph('LAPORAN DATA ANGGOTA', styles['JudulLaporan']))
        story.append(Paragraph(f'Per tanggal: {fmt_date(datetime.now().date())}', styles['SubJudul']))

        # ====== I. PROFIL ======
        story.append(Paragraph('I. Data Pribadi Anggota', styles['SectionTitle']))
        profile_data = [
            [Paragraph('Nama Lengkap', styles['InfoLabel']), Paragraph(': ' + anggota.nama, styles['InfoValue'])],
            [Paragraph('NIK', styles['InfoLabel']), Paragraph(': ' + anggota.nik, styles['InfoValue'])],
            [Paragraph('Telepon', styles['InfoLabel']), Paragraph(': ' + (anggota.telepon or '-'), styles['InfoValue'])],
            [Paragraph('Tanggal Bergabung', styles['InfoLabel']), Paragraph(': ' + fmt_date(anggota.tanggal_bergabung), styles['InfoValue'])],
            [Paragraph('Status', styles['InfoLabel']), Paragraph(': ' + anggota.get_status_display(), styles['InfoValue'])],
            [Paragraph('Alamat', styles['InfoLabel']), Paragraph(': ' + (anggota.alamat or '-'), styles['InfoValue'])],
        ]
        pt = Table(profile_data, colWidths=[4*cm, 12*cm])
        pt.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 2),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ]))
        story.append(pt)

        # ====== SUMMARY CARD ======
        story.append(Spacer(1, 4*mm))
        sh = ParagraphStyle('_sh', parent=tc, alignment=TA_CENTER, textColor=white)
        sb = ParagraphStyle('_sb', parent=tc, alignment=TA_CENTER)
        summary_data = [
            [Paragraph('<b>Total Iuran</b>', sh), Paragraph('<b>Total Simpanan</b>', sh), Paragraph('<b>Total Pinjaman</b>', sh)],
            [Paragraph(f'<b>{fmt_kg(total_iuran_kg)} kg</b><br/>{fmt_rp(total_iuran_rp)}', sb),
             Paragraph(f'<b>{fmt_rp(total_simpanan)}</b>', sb),
             Paragraph(f'<b>{fmt_rp(total_pinjaman)}</b>', sb)],
        ]
        st = Table(summary_data, colWidths=[5.3*cm, 5.3*cm, 5.3*cm])
        st.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#d97706')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#7c3aed')),
            ('BACKGROUND', (2, 0), (2, 0), colors.HexColor('#dc2626')),
            ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#fffbeb')),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#f5f3ff')),
            ('BACKGROUND', (2, 1), (2, 1), colors.HexColor('#fef2f2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, 1), 10),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
        ]))
        story.append(st)

        # ====== II. IURAN PANEN ======
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph('II. Riwayat Iuran Panen Gabah', styles['SectionTitle']))

        if iuran_qs.exists():
            iuran_data = [[
                hc('<b>No</b>'), hc('<b>Tanggal</b>'), hc('<b>Periode</b>'),
                hr('<b>Jumlah (kg)</b>'), hr('<b>Harga/100kg</b>'), hr('<b>Nilai (Rp)</b>'),
            ]]
            for idx, i in enumerate(iuran_qs, 1):
                iuran_data.append([
                    c(str(idx)), Paragraph(i.tanggal.strftime('%d/%m/%Y'), tc),
                    Paragraph(i.periode, tc), r(fmt_kg(i.jumlah_kg)),
                    r(fmt_rp(i.harga_per_100kg)), rb(fmt_rp(i.nilai_rp)),
                ])
            iuran_data.append([
                '', '', Paragraph('<b>TOTAL</b>', tcb),
                rb(fmt_kg(total_iuran_kg)), '', rb(fmt_rp(total_iuran_rp)),
            ])
            it = Table(iuran_data, colWidths=[1*cm, 2.5*cm, 2.5*cm, 2.5*cm, 3*cm, 3.5*cm])
            it.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d97706')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fef3c7')),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#d97706')),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(it)
        else:
            story.append(Paragraph('<i>Belum ada data iuran panen.</i>', empty_style()))

        # ====== III. SIMPANAN ======
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph('III. Riwayat Simpanan Uang', styles['SectionTitle']))

        if simpanan_qs.exists():
            simp_data = [[
                hc('<b>No</b>'), hc('<b>Tanggal</b>'), hr('<b>Jumlah (Rp)</b>'),
                hc('<b>Bunga</b>'), hc('<b>Jatuh Tempo</b>'),
                hc('<b>Status</b>'), hc('<b>Keterangan</b>'),
            ]]
            total_simp_rp = Decimal('0')
            for idx, s in enumerate(simpanan_qs, 1):
                total_simp_rp += s.jumlah_rp
                simp_data.append([
                    c(str(idx)), Paragraph(s.tanggal.strftime('%d/%m/%Y'), tc),
                    rb(fmt_rp(s.jumlah_rp)), c(f'{float(s.bunga_persen):.1f}%'),
                    c(s.jatuh_tempo.strftime('%d/%m/%Y') if s.jatuh_tempo else '-'),
                    c(s.get_status_display()), Paragraph(s.keterangan or '-', tc),
                ])
            simp_data.append([
                '', Paragraph('<b>TOTAL</b>', tcb), rb(fmt_rp(total_simp_rp)), '', '', '', '',
            ])
            spt = Table(simp_data, colWidths=[1*cm, 2.2*cm, 3*cm, 1.5*cm, 2.5*cm, 1.8*cm, 4*cm])
            spt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#ede9fe')),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#7c3aed')),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(spt)
        else:
            story.append(Paragraph('<i>Belum ada data simpanan.</i>', empty_style()))

        # ====== IV. PINJAMAN ======
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph('IV. Riwayat Peminjaman', styles['SectionTitle']))

        if pinjaman_qs.exists():
            pinj_data = [[
                hc('<b>No</b>'), hc('<b>Tanggal</b>'), hr('<b>Jumlah (Rp)</b>'),
                hc('<b>Bunga</b>'), hc('<b>Jatuh Tempo</b>'),
                hc('<b>Status</b>'), hc('<b>Keterangan</b>'),
            ]]
            total_pinj_rp = Decimal('0')
            for idx, p in enumerate(pinjaman_qs, 1):
                total_pinj_rp += p.jumlah_rp
                pinj_data.append([
                    c(str(idx)), Paragraph(p.tanggal.strftime('%d/%m/%Y'), tc),
                    rb(fmt_rp(p.jumlah_rp)), c(f'{float(p.bunga_persen):.1f}%'),
                    c(p.jatuh_tempo.strftime('%d/%m/%Y') if p.jatuh_tempo else '-'),
                    c(p.get_status_display()), Paragraph(p.keterangan or '-', tc),
                ])
            pinj_data.append([
                '', Paragraph('<b>TOTAL</b>', tcb), rb(fmt_rp(total_pinj_rp)), '', '', '', '',
            ])
            pjt = Table(pinj_data, colWidths=[1*cm, 2.2*cm, 3*cm, 1.5*cm, 2.5*cm, 1.8*cm, 4*cm])
            pjt.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc2626')),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fee2e2')),
                ('LINEABOVE', (0, -1), (-1, -1), 1, colors.HexColor('#dc2626')),
                ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e2e8f0')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(pjt)
        else:
            story.append(Paragraph('<i>Belum ada data pinjaman.</i>', empty_style()))

        # ====== TANDA TANGAN ======
        story.append(Spacer(1, 20*mm))
        now = datetime.now()
        bulan_map = {
            1: 'Januari', 2: 'Februari', 3: 'Maret', 4: 'April',
            5: 'Mei', 6: 'Juni', 7: 'Juli', 8: 'Agustus',
            9: 'September', 10: 'Oktober', 11: 'November', 12: 'Desember',
        }
        tanggal_cetak = f'{now.day} {bulan_map.get(now.month, "")} {now.year}'

        tgl_s = ParagraphStyle('_tgl', parent=styles['InfoLabel'], alignment=TA_CENTER, fontSize=9)
        story.append(Paragraph(f'Madureso, {tanggal_cetak}', tgl_s))
        story.append(Paragraph('Mengetahui,', tgl_s))
        story.append(Spacer(1, 3*mm))

        ttd_data = [
            [Paragraph('Ketua Koperasi', styles['TtdJabatan']),
             Paragraph('Sekretaris', styles['TtdJabatan'])],
            [Spacer(1, 18*mm), Spacer(1, 18*mm)],
            [Paragraph('___________________________', styles['TtdNama']),
             Paragraph('___________________________', styles['TtdNama'])],
            [Paragraph('Nama Ketua', styles['TtdNama']),
             Paragraph('Nama Sekretaris', styles['TtdNama'])],
        ]
        ttd_t = Table(ttd_data, colWidths=[8*cm, 8*cm])
        ttd_t.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(ttd_t)

        # ====== FOOTER ======
        story.append(Spacer(1, 10*mm))
        story.append(HRFlowable(width='40%', thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=2*mm))
        story.append(Paragraph(
            f'Dokumen ini dicetak secara otomatis oleh Sistem Informasi Koperasi Gabah | {tanggal_cetak}',
            styles['Footer']
        ))

        # ====== BUILD ======
        doc.build(story)
        buffer.seek(0)

        filename = f'Laporan_{anggota.nama.replace(" ", "_")}_{now.strftime("%Y%m%d")}.pdf'
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response

    except Exception as e:
        return HttpResponse(
            f'<html><body style="font-family:monospace; padding:30px; background:#fef2f2;">'
            f'<h2 style="color:#dc2626;">Error saat generate PDF</h2>'
            f'<pre style="background:#fff; padding:20px; border-radius:8px; border:1px solid #fecaca; '
            f'font-size:13px; color:#1e293b; white-space:pre-wrap;">'
            f'{traceback.format_exc()}</pre>'
            f'</body></html>',
            content_type='text/html', status=500,
        )
