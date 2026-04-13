from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import DonViBenTrong, DonViBenNgoai, VanBanDi, LichSuHoatDong, PheDuyet, PhatHanh, UserAccount
import json

# --- TRANG CHỦ & ĐĂNG NHẬP ---
def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

# --- QUẢN LÝ VĂN BẢN ĐẾN ---
def van_ban_den_index(request):
    return render(request, 'van_ban_den/index.html')

# --- QUẢN LÝ VĂN BẢN ĐI ---
def van_ban_di_index(request):
    so_ky_hieu = request.GET.get('so_ky_hieu', '')
    trich_yeu   = request.GET.get('trich_yeu', '')
    loai_vb     = request.GET.get('loai_vb', '')
    don_vi      = request.GET.get('don_vi', '')
    page_number = request.GET.get('page', 1)
    page_size   = 8

    vbs = VanBanDi.objects.select_related('DonViNgoaiID', 'DonViTrongID', 'UserID').order_by('-VanBanDiID')
    if so_ky_hieu:
        vbs = vbs.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        vbs = vbs.filter(TrichYeu__icontains=trich_yeu)
    if loai_vb:
        vbs = vbs.filter(LoaiVanBan__icontains=loai_vb)
    if don_vi:
        vbs = vbs.filter(
            Q(DonViNgoaiID__TenDonVi__icontains=don_vi) |
            Q(DonViTrongID__TenDonVi__icontains=don_vi)
        )

    paginator  = Paginator(vbs, page_size)
    page_obj   = paginator.get_page(page_number)
    don_vi_ngoai_list = DonViBenNgoai.objects.all()
    don_vi_trong_list = DonViBenTrong.objects.all()

    # Tính range trang hiển thị (tối đa 3 trang xung quanh trang hiện tại)
    current = page_obj.number
    total   = paginator.num_pages
    start   = max(current - 1, 1)
    end     = min(start + 2, total)
    start   = max(end - 2, 1)
    page_range = range(start, end + 1)

    return render(request, 'van_ban_di/index.html', {
        'page_obj': page_obj,
        'paginator': paginator,
        'page_range': page_range,
        'don_vi_ngoai_list': don_vi_ngoai_list,
        'don_vi_trong_list': don_vi_trong_list,
        'so_ky_hieu': so_ky_hieu,
        'trich_yeu': trich_yeu,
        'loai_vb': loai_vb,
        'don_vi': don_vi,
    })

def api_vbdi_chi_tiet(request, pk):
    vb = get_object_or_404(VanBanDi, pk=pk)
    return JsonResponse({
        'status': 'success',
        'data': {
            'id': vb.VanBanDiID,
            'so_ky_hieu': vb.SoKyHieu,
            'trich_yeu': vb.TrichYeu or '',
            'loai_vb': vb.LoaiVanBan or '',
            'don_vi_ngoai': vb.DonViNgoaiID.TenDonVi if vb.DonViNgoaiID else '',
            'don_vi_trong': vb.DonViTrongID.TenDonVi if vb.DonViTrongID else '',
            'nguoi_soan': vb.UserID.HoTen if vb.UserID else '',
            'ngay_ban_hanh': vb.NgayBanHanh.strftime('%d/%m/%Y') if vb.NgayBanHanh else '',
            'trang_thai': vb.get_TrangThai_display(),
            'tep_dinh_kem': str(vb.TepDinhKem) if vb.TepDinhKem else '',
        }
    })

def api_vbdi_them_moi(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        # Nhận cả form data lẫn file
        vb = VanBanDi()
        vb.SoKyHieu    = request.POST.get('so_ky_hieu', '')
        vb.TrichYeu    = request.POST.get('trich_yeu', '')
        vb.LoaiVanBan  = request.POST.get('loai_vb', '')
        vb.NgayBanHanh = request.POST.get('ngay_ban_hanh') or None
        don_vi_ngoai_id = request.POST.get('don_vi_ngoai_id')
        don_vi_trong_id = request.POST.get('don_vi_trong_id')
        if don_vi_ngoai_id:
            vb.DonViNgoaiID = get_object_or_404(DonViBenNgoai, pk=don_vi_ngoai_id)
        if don_vi_trong_id:
            vb.DonViTrongID = get_object_or_404(DonViBenTrong, pk=don_vi_trong_id)
        if request.FILES.get('tep_dinh_kem'):
            vb.TepDinhKem = request.FILES['tep_dinh_kem']
        vb.TrangThai = request.POST.get('trang_thai', VanBanDi.TrangThaiChoices.DU_THAO)
        vb.save()
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'THEM_MOI', 'Thêm mới văn bản', None, vb.TrangThai)
        return JsonResponse({'status': 'success', 'id': vb.VanBanDiID})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_cap_nhat(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb  = get_object_or_404(VanBanDi, pk=pk)
        cu  = vb.TrangThai
        vb.SoKyHieu   = request.POST.get('so_ky_hieu', vb.SoKyHieu)
        vb.TrichYeu   = request.POST.get('trich_yeu', vb.TrichYeu)
        vb.LoaiVanBan = request.POST.get('loai_vb', vb.LoaiVanBan)
        ngay = request.POST.get('ngay_ban_hanh')
        if ngay: vb.NgayBanHanh = ngay
        don_vi_ngoai_id = request.POST.get('don_vi_ngoai_id')
        don_vi_trong_id = request.POST.get('don_vi_trong_id')
        if don_vi_ngoai_id:
            vb.DonViNgoaiID = get_object_or_404(DonViBenNgoai, pk=don_vi_ngoai_id)
        if don_vi_trong_id:
            vb.DonViTrongID = get_object_or_404(DonViBenTrong, pk=don_vi_trong_id)
        trang_thai = request.POST.get('trang_thai')
        if trang_thai: vb.TrangThai = trang_thai
        if request.FILES.get('tep_dinh_kem'):
            vb.TepDinhKem = request.FILES['tep_dinh_kem']
        elif request.POST.get('xoa_file') == '1':
            vb.TepDinhKem = None
        vb.save()
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'CAP_NHAT', 'Cập nhật văn bản', cu, vb.TrangThai)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_xoa(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb = get_object_or_404(VanBanDi, pk=pk)
        vb.delete()
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_phe_duyet(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb   = get_object_or_404(VanBanDi, pk=pk)
        data = json.loads(request.body)
        cu   = vb.TrangThai
        chap_nhan = data.get('chap_nhan', True)
        pd = PheDuyet()
        pd.VanBanDiID     = vb
        pd.UserID         = UserAccount.objects.first()  # TODO: dùng request.user khi có auth
        pd.NgayPheDuyet   = timezone.now()
        pd.TrangThaiDuyet = chap_nhan
        pd.GhiChu         = data.get('ghi_chu', '')
        pd.save()
        vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHE_DUYET if chap_nhan else VanBanDi.TrangThaiChoices.DU_THAO
        vb.save()
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'PHE_DUYET', 'Phê duyệt văn bản', cu, vb.TrangThai)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_phat_hanh(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb   = get_object_or_404(VanBanDi, pk=pk)
        data = json.loads(request.body)
        cu   = vb.TrangThai
        ph = PhatHanh()
        ph.VanBanDiID    = vb
        ph.UserID        = UserAccount.objects.first()  # TODO: dùng request.user khi có auth
        ph.TieuDe        = data.get('trich_yeu', vb.TrichYeu)
        ph.NgayPhatHanh  = data.get('ngay_ban_hanh') or timezone.now()
        ph.TrangThai     = 'DA_PHAT_HANH'
        ph.save()
        vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHAT_HANH
        if data.get('ngay_ban_hanh'):
            vb.NgayBanHanh = data.get('ngay_ban_hanh')
        vb.save()
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'PHAT_HANH', 'Phát hành văn bản', cu, vb.TrangThai)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_lich_su(request, pk):
    lich_su = LichSuHoatDong.objects.filter(
        LoaiDoiTuong='VanBanDi', DoiTuongID=pk
    ).select_related('UserID').order_by('-ThoiGianCapNhat')
    data = [{
        'thoi_gian': ls.ThoiGianCapNhat.strftime('%d/%m/%Y %H:%M'),
        'nguoi_thuc_hien': ls.UserID.HoTen if ls.UserID else '',
        'ma_van_ban': str(pk),
        'noi_dung': ls.NoiDungThayDoi or '',
        'trang_thai_cu': ls.TrangThaiCu or '',
        'trang_thai_moi': ls.TrangThaiMoi or '',
    } for ls in lich_su]
    return JsonResponse({'status': 'success', 'data': data})

def _ghi_lich_su(request, loai, doi_tuong_id, hanh_dong, noi_dung, trang_thai_cu, trang_thai_moi):
    try:
        ls = LichSuHoatDong()
        ls.UserID        = UserAccount.objects.first()  # TODO: dùng request.user khi có auth
        ls.LoaiDoiTuong  = loai
        ls.DoiTuongID    = doi_tuong_id
        ls.HanhDong      = hanh_dong
        ls.NoiDungThayDoi = noi_dung
        ls.TrangThaiCu   = trang_thai_cu
        ls.TrangThaiMoi  = trang_thai_moi
        ls.save()
    except Exception:
        pass

# --- QUẢN LÝ NGƯỜI DÙNG ---
def quan_ly_nguoi_dung_index(request):
    return render(request, 'quan_ly_nguoi_dung/index.html')

def thong_tin_nguoi_dung(request):
    return render(request, 'quan_ly_nguoi_dung/thong_tin.html')

# --- QUẢN LÝ ĐƠN VỊ ---
def quan_ly_don_vi_ben_ngoai(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    page_number = request.GET.get('page', 1)
    page_size = 5

    units = DonViBenNgoai.objects.all().order_by('-pk')
    if query_name:
        units = units.filter(TenDonVi__icontains=query_name)
    if query_address:
        units = units.filter(DiaChi__icontains=query_address)
    if query_contact:
        units = units.filter(NguoiLienHe__icontains=query_contact)

    paginator = Paginator(units, page_size)
    page_obj  = paginator.get_page(page_number)

    if request.GET.get('ajax') == '1':
        unit_list = [{'id': u.DonViNgoaiID, 'name': u.TenDonVi, 'address': u.DiaChi,
                      'phone': u.SoDienThoai, 'email': u.Email, 'contact': u.NguoiLienHe}
                     for u in page_obj]
        return JsonResponse({'status': 'success', 'data': unit_list,
                             'pagination': {'total_count': paginator.count, 'total_pages': paginator.num_pages,
                                            'current_page': page_obj.number, 'has_next': page_obj.has_next(),
                                            'has_previous': page_obj.has_previous()}})

    return render(request, 'quan_ly_don_vi/ben_ngoai.html', {
        'page_obj': page_obj, 'query_name': query_name,
        'query_address': query_address, 'query_contact': query_contact
    })

def quan_ly_don_vi_ben_trong(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    page_number = request.GET.get('page', 1)
    page_size = 5

    units = DonViBenTrong.objects.all().order_by('-pk')
    if query_name:
        units = units.filter(TenDonVi__icontains=query_name)
    if query_address:
        units = units.filter(DiaChi__icontains=query_address)
    if query_contact:
        units = units.filter(NguoiLienHe__icontains=query_contact)

    paginator = Paginator(units, page_size)
    page_obj  = paginator.get_page(page_number)

    if request.GET.get('ajax') == '1':
        unit_list = [{'id': u.DonViTrongID, 'name': u.TenDonVi, 'address': u.DiaChi,
                      'phone': u.SoDienThoai, 'email': u.Email, 'contact': u.NguoiLienHe}
                     for u in page_obj]
        return JsonResponse({'status': 'success', 'data': unit_list,
                             'pagination': {'total_count': paginator.count, 'total_pages': paginator.num_pages,
                                            'current_page': page_obj.number, 'has_next': page_obj.has_next(),
                                            'has_previous': page_obj.has_previous()}})

    return render(request, 'quan_ly_don_vi/ben_trong.html', {
        'page_obj': page_obj, 'query_name': query_name,
        'query_address': query_address, 'query_contact': query_contact
    })

def api_upsert_don_vi(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit_type = data.get('type')
            unit_id   = data.get('id')
            model = DonViBenTrong if unit_type == 'trong' else DonViBenNgoai
            if unit_id:
                unit = get_object_or_404(model, pk=unit_id)
            else:
                unit = model()
            unit.TenDonVi    = data.get('name')
            unit.DiaChi      = data.get('address')
            unit.SoDienThoai = data.get('phone')
            unit.Email       = data.get('email')
            unit.NguoiLienHe = data.get('contact')
            unit.save()
            return JsonResponse({'status': 'success', 'message': 'Lưu thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def api_delete_don_vi(request):
    if request.method == 'POST':
        try:
            data      = json.loads(request.body)
            unit_type = data.get('type')
            unit_id   = data.get('id')
            model = DonViBenTrong if unit_type == 'trong' else DonViBenNgoai
            unit  = get_object_or_404(model, pk=unit_id)
            unit.delete()
            return JsonResponse({'status': 'success', 'message': 'Xóa thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

# --- XỬ LÝ VĂN BẢN ĐIỀU HÀNH ---
def xu_ly_van_ban_index(request):
    return render(request, 'xu_ly_van_ban/index.html')

def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')

def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')

def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')

def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')


# --- TRANG CHỦ & ĐĂNG NHẬP ---
def index(request):
    """View cho trang Dashboard"""
    return render(request, 'index.html')

def login(request):
    """View cho trang Đăng nhập"""
    return render(request, 'login.html')

# --- QUẢN LÝ VĂN BẢN ĐẾN ---
def van_ban_den_index(request):
    return render(request, 'van_ban_den/index.html')

# --- QUẢN LÝ NGƯỜI DÙNG ---
def quan_ly_nguoi_dung_index(request):
    return render(request, 'quan_ly_nguoi_dung/index.html')

def thong_tin_nguoi_dung(request):
    return render(request, 'quan_ly_nguoi_dung/thong_tin.html')

# --- QUẢN LÝ ĐƠN VỊ ---
def quan_ly_don_vi_ben_ngoai(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    page_number = request.GET.get('page', 1)
    page_size = 5  # Giới hạn duy nhất cho quản lý đơn vị

    units = DonViBenNgoai.objects.all().order_by('-pk')
    
    if query_name:
        units = units.filter(TenDonVi__icontains=query_name)
    if query_address:
        units = units.filter(DiaChi__icontains=query_address)
    if query_contact:
        units = units.filter(NguoiLienHe__icontains=query_contact)

    paginator = Paginator(units, page_size)
    page_obj = paginator.get_page(page_number)

    if request.GET.get('ajax') == '1':
        unit_list = []
        for u in page_obj:
            unit_list.append({
                'id': u.DonViNgoaiID,
                'name': u.TenDonVi,
                'address': u.DiaChi,
                'phone': u.SoDienThoai,
                'email': u.Email,
                'contact': u.NguoiLienHe
            })
        return JsonResponse({
            'status': 'success',
            'data': unit_list,
            'pagination': {
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    return render(request, 'quan_ly_don_vi/ben_ngoai.html', {
        'page_obj': page_obj,
        'query_name': query_name,
        'query_address': query_address,
        'query_contact': query_contact
    })

def quan_ly_don_vi_ben_trong(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    page_number = request.GET.get('page', 1)
    page_size = 5  # Giới hạn duy nhất cho quản lý đơn vị

    units = DonViBenTrong.objects.all().order_by('-pk')
    
    if query_name:
        units = units.filter(TenDonVi__icontains=query_name)
    if query_address:
        units = units.filter(DiaChi__icontains=query_address)
    if query_contact:
        units = units.filter(NguoiLienHe__icontains=query_contact)

    paginator = Paginator(units, page_size)
    page_obj = paginator.get_page(page_number)

    if request.GET.get('ajax') == '1':
        unit_list = []
        for u in page_obj:
            unit_list.append({
                'id': u.DonViTrongID,
                'name': u.TenDonVi,
                'address': u.DiaChi,
                'phone': u.SoDienThoai,
                'email': u.Email,
                'contact': u.NguoiLienHe
            })
        return JsonResponse({
            'status': 'success',
            'data': unit_list,
            'pagination': {
                'total_count': paginator.count,
                'total_pages': paginator.num_pages,
                'current_page': page_obj.number,
                'has_next': page_obj.has_next(),
                'has_previous': page_obj.has_previous(),
            }
        })

    return render(request, 'quan_ly_don_vi/ben_trong.html', {
        'page_obj': page_obj,
        'query_name': query_name,
        'query_address': query_address,
        'query_contact': query_contact
    })

def api_upsert_don_vi(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit_type = data.get('type')  # 'trong' or 'ngoai'
            unit_id = data.get('id')
            
            model = DonViBenTrong if unit_type == 'trong' else DonViBenNgoai
            
            if unit_id:
                # Update
                if unit_type == 'trong':
                    unit = get_object_or_404(DonViBenTrong, DonViTrongID=unit_id)
                else:
                    unit = get_object_or_404(DonViBenNgoai, DonViNgoaiID=unit_id)
            else:
                # Create
                unit = model()

            unit.TenDonVi = data.get('name')
            unit.DiaChi = data.get('address')
            unit.SoDienThoai = data.get('phone')
            unit.Email = data.get('email')
            unit.NguoiLienHe = data.get('contact')
            unit.save()

            return JsonResponse({'status': 'success', 'message': 'Lưu thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def api_delete_don_vi(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit_type = data.get('type')
            unit_id = data.get('id')
            
            if unit_type == 'trong':
                unit = get_object_or_404(DonViBenTrong, DonViTrongID=unit_id)
            else:
                unit = get_object_or_404(DonViBenNgoai, DonViNgoaiID=unit_id)
            
            unit.delete()
            return JsonResponse({'status': 'success', 'message': 'Xóa thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

# --- XỬ LÝ VĂN BẢN ĐIỀU HÀNH ---
def xu_ly_van_ban_index(request):
    return render(request, 'xu_ly_van_ban/index.html')

def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')

def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')

def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')

def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')
