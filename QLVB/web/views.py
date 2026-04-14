
from .models import VanBanDi, PheDuyet, PhatHanh
import json
from datetime import timedelta

# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

# IMPORT CHO HỆ THỐNG THÔNG BÁO LỖI (MESSAGES)
from .forms import LoginForm
from .forms import VanBanDenForm
from .models import DonViBenTrong, UserAccount, VaiTro
from .models import PhanCong, ChuyenTiep, BaoCao
from .models import VanBanDen, DonViBenNgoai, LichSuHoatDong
from .models import VanBanDi, PheDuyet, PhatHanh


# --- TRANG CHỦ ---
@login_required
def index(request):
    """View cho trang Dashboard - Chỉ cho phép người đã đăng nhập"""
    return render(request, 'index.html')


# --- HỆ THỐNG ĐĂNG NHẬP / ĐĂNG XUẤT ---
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            return redirect('index')
        else:
            # Nếu form không hợp lệ (sai pass, thiếu user), in lỗi ra terminal để xem
            print(form.errors)
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# --- QUẢN LÝ VĂN BẢN ĐẾN ---
def van_ban_den_index(request):
    danh_sach = VanBanDen.objects.select_related('DonViNgoaiID').all().order_by('-VanBanDenID')
    don_vi_ngoai = DonViBenNgoai.objects.all()

    so_ky_hieu = request.GET.get('so_ky_hieu', '')
    trich_yeu = request.GET.get('trich_yeu', '')
    don_vi_id = request.GET.get('don_vi', '')

    if so_ky_hieu:
        danh_sach = danh_sach.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        danh_sach = danh_sach.filter(TrichYeu__icontains=trich_yeu)
    if don_vi_id:
        danh_sach = danh_sach.filter(DonViNgoaiID_id=don_vi_id)

    from django.core.paginator import Paginator
    paginator = Paginator(danh_sach, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Tạo query string cho các filter (loại bỏ tham số page)
    q = request.GET.copy()
    if 'page' in q:
        del q['page']
    query_string = f"&{q.urlencode()}" if q else ""

    return render(request, 'van_ban_den/index.html', {
        'page_obj': page_obj,
        'danh_sach': page_obj.object_list,
        'don_vi_ngoai': don_vi_ngoai,
        'tong_so': paginator.count,
        'query_string': query_string
    })


@csrf_exempt
def van_ban_den_them(request):
    if request.method == 'POST':
        try:
            form = VanBanDenForm(request.POST, request.FILES)
            if form.is_valid():
                vbd = form.save(user=request.user if request.user.is_authenticated else None)

                LichSuHoatDong.objects.create(
                    UserID=request.user if request.user.is_authenticated else None,
                    LoaiDoiTuong='VanBanDen',
                    DoiTuongID=vbd.VanBanDenID,
                    HanhDong='Thêm',
                    NoiDungThayDoi=f'Thêm mới văn bản đến: {vbd.SoKyHieu}'
                )
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': str(form.errors)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})


def van_ban_den_xem(request, pk):
    from .models import PhanCong, ChuyenTiep, BaoCao
    vbd = VanBanDen.objects.filter(pk=pk).first()
    if not vbd:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy'})

    qua_trinh_xu_ly = []

    # 1. Lấy thông tin Phân công
    phan_congs = PhanCong.objects.filter(VanBanDenID=vbd).select_related('UserID').order_by('NgayPhanCong')
    for pc in phan_congs:
        tag_name = pc.TrangThaiXuLy or "Phân công"
        tag_class = "vbd-process-tag-active" if tag_name == 'Đang xử lý' else "vbd-process-tag-blue"

        qua_trinh_xu_ly.append({
            'time': pc.NgayPhanCong,
            'tag': tag_name,
            'tag_class': tag_class,
            'icon': 'fa-user-check',
            'chuyen_toi': f"{pc.UserID.HoTen} ({pc.UserID.username})" if pc.UserID else "Chưa xác định",
            'dong_xu_ly': "",
            'action': pc.GhiChu or f"Giao xử lý cho {pc.UserID.HoTen if pc.UserID else 'cán bộ'}"
        })

    # 2. Lấy thông tin Chuyển tiếp
    chuyen_tieps = ChuyenTiep.objects.filter(VanBanDenID=vbd).select_related('UserID').order_by('NgayChuyenTiep')
    for ct in chuyen_tieps:
        qua_trinh_xu_ly.append({
            'time': ct.NgayChuyenTiep,
            'tag': "Chuyển tiếp",
            'tag_class': "vbd-process-tag-blue",
            'icon': 'fa-share-square',
            'chuyen_toi': f"{ct.UserID.HoTen} ({ct.UserID.username})" if ct.UserID else "Chưa xác định",
            'dong_xu_ly': "",
            'action': "Chuyển tiếp văn bản cho đơn vị/cá nhân khác"
        })

    # 3. Lấy thông tin Báo cáo (Chỉ lấy loại Phản hồi - Sai sót/Không phù hợp)
    bao_caos = BaoCao.objects.filter(VanBanDenID=vbd, LoaiBaoCao='PHAN_HOI').select_related('UserID').order_by(
        'NgayBaoCao')
    for bc in bao_caos:
        qua_trinh_xu_ly.append({
            'time': bc.NgayBaoCao,
            'tag': "Phản hồi",
            'tag_class': "vbd-process-tag-gray",
            'icon': 'fa-exclamation-triangle',
            'chuyen_toi': f"{bc.UserID.HoTen} ({bc.UserID.username})" if bc.UserID else "Nguời báo cáo",
            'dong_xu_ly': "",
            'action': bc.GhiChu or "Báo cáo văn bản sai sót/không phù hợp"
        })

    # Sắp xếp theo thời gian
    qua_trinh_xu_ly.sort(key=lambda x: x['time'] if x['time'] else timezone.now(), reverse=False)

    # Xóa field thời gian trước khi trả về JSON để tránh lỗi serialize nếu cần,
    # nhưng ở đây ta chỉ cần extract thông tin string
    for item in qua_trinh_xu_ly:
        if 'time' in item: del item['time']

    return JsonResponse({
        'status': 'success',
        'data': {
            'id': vbd.VanBanDenID,
            'so_ky_hieu': vbd.SoKyHieu,
            'trich_yeu': vbd.TrichYeu,
            'loai_van_ban': vbd.LoaiVanBan,
            'ngay_ban_hanh': vbd.NgayBanHanh.strftime('%Y-%m-%d') if vbd.NgayBanHanh else '',
            'ngay_nhan': vbd.NgayNhan.strftime('%Y-%m-%d') if vbd.NgayNhan else '',
            'don_vi_ngoai_ten': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else '',
            'don_vi_ngoai_id': vbd.DonViNgoaiID_id,
            'tep_dinh_kem': vbd.TepDinhKem.url if vbd.TepDinhKem else '',
            'tep_name': vbd.TepDinhKem.name.split('/')[-1] if vbd.TepDinhKem else '',
            'trang_thai': vbd.TrangThai,
            'qua_trinh_xu_ly': qua_trinh_xu_ly
        }
    })


@csrf_exempt
def van_ban_den_sua(request, pk):
    if request.method == 'POST':
        vbd = VanBanDen.objects.filter(pk=pk).first()
        if not vbd:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy'})

        vbd_initial = VanBanDen.objects.filter(pk=pk).values().first()
        old_data = {
            'Số ký hiệu': vbd.SoKyHieu,
            'Trích yếu': vbd.TrichYeu,
            'Loại văn bản': vbd.LoaiVanBan,
            'Ngày ban hành': vbd.NgayBanHanh.strftime('%d/%m/%Y') if vbd.NgayBanHanh else 'Trống',
            'Ngày nhận': vbd.NgayNhan.strftime('%d/%m/%Y') if vbd.NgayNhan else 'Trống',
            'Đơn vị gửi': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống',
            'Trạng thái': 'Đang xử lý' if vbd.TrangThai != 'HOAN_THANH' else 'Hoàn thành',
            'Tệp đính kèm': vbd.TepDinhKem.name.split('/')[-1] if vbd.TepDinhKem else 'Trống'
        }

        form = VanBanDenForm(request.POST, request.FILES)
        if form.is_valid():
            vbd = form.save(user=request.user if request.user.is_authenticated else None, instance=vbd)
            
            # Đảm bảo dữ liệu mới được load từ DB để so sánh chính xác nhất
            vbd.refresh_from_db()

            # So sánh dữ liệu mới
            new_data = {
                'Số ký hiệu': vbd.SoKyHieu,
                'Trích yếu': vbd.TrichYeu,
                'Loại văn bản': vbd.LoaiVanBan,
                'Ngày ban hành': vbd.NgayBanHanh.strftime('%d/%m/%Y') if vbd.NgayBanHanh else 'Trống',
                'Ngày nhận': vbd.NgayNhan.strftime('%d/%m/%Y') if vbd.NgayNhan else 'Trống',
                'Đơn vị gửi': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống',
                'Trạng thái': 'Đang xử lý' if vbd.TrangThai != 'HOAN_THANH' else 'Hoàn thành',
                'Tệp đính kèm': vbd.TepDinhKem.name.split('/')[-1] if vbd.TepDinhKem else 'Trống'
            }

            changes = []
            for field, old_val in old_data.items():
                new_val = new_data.get(field)
                if old_val != new_val:
                    changes.append(f"{field}: {old_val} -> {new_val}")

            if changes:
                try:
                    # Nếu có từ 2 thay đổi trở lên thì liệt kê, nếu 1 thì ghi trực tiếp
                    if len(changes) > 1:
                        content = "Thay đổi:\n- " + "\n- ".join(changes)
                    else:
                        content = "Thay đổi: " + changes[0]
                        
                    LichSuHoatDong.objects.create(
                        UserID=request.user if request.user.is_authenticated else None,
                        LoaiDoiTuong='VanBanDen',
                        DoiTuongID=vbd.VanBanDenID,
                        HanhDong='Cập nhật',
                        NoiDungThayDoi=content
                    )
                except Exception as e:
                    print(f"Lỗi lưu lịch sử: {e}")

            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': str(form.errors)})
    return JsonResponse({'status': 'error'})


@csrf_exempt
def van_ban_den_xoa(request, pk):
    if request.method == 'POST':
        vbd = VanBanDen.objects.filter(pk=pk).first()
        if vbd:
            so_k_h = vbd.SoKyHieu
            vbd.delete()
            LichSuHoatDong.objects.create(
                UserID=request.user if request.user.is_authenticated else None,
                LoaiDoiTuong='VanBanDen',
                DoiTuongID=pk,
                HanhDong='Xóa',
                NoiDungThayDoi=f'Đã xóa văn bản {so_k_h}'
            )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})


def van_ban_den_lich_su(request):
    pk = request.GET.get('id')
    lich_su = LichSuHoatDong.objects.filter(LoaiDoiTuong='VanBanDen')
    if pk:
        try:
            lich_su = lich_su.filter(DoiTuongID=int(pk))
        except (ValueError, TypeError):
            lich_su = lich_su.none()

    vbd = VanBanDen.objects.filter(pk=pk).first() if pk else None
    lich_su = lich_su.order_by('-ThoiGianCapNhat')

    data = []
    for ls in lich_su:
        data.append({
            'ThoiGianCapNhat': ls.ThoiGianCapNhat.strftime('%d/%m/%Y %H:%M') if ls.ThoiGianCapNhat else '',
            'NguoiThucHien': ls.UserID.HoTen if ls.UserID and ls.UserID.HoTen else (
                ls.UserID.username if ls.UserID else 'Hệ thống'),
            'HanhDong': ls.HanhDong,
            'NoiDungThayDoi': ls.NoiDungThayDoi,
            'SoKyHieu': vbd.SoKyHieu if vbd else '',
            'TrichYeu': vbd.TrichYeu if vbd else ''
        })
    return JsonResponse({'status': 'success', 'data': data})


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

def thong_tin_view(request):
    return render(request, 'thong_tin.html')

# --- API NGƯỜI DÙNG ---
def api_nguoi_dung_list(request):
    query_username = request.GET.get('username', '')
    query_fullname = request.GET.get('fullname', '')
    query_dept = request.GET.get('dept', '')
    query_status = request.GET.get('status', '')
    user_id = request.GET.get('id')
    page_number = request.GET.get('page', 1)
    page_size = 5

    users = UserAccount.objects.all().order_by('SoThuTu', '-pk')

    if user_id:
        users = users.filter(UserID=user_id)
    if query_username:
        users = users.filter(username__icontains=query_username)
    if query_fullname:
        users = users.filter(HoTen__icontains=query_fullname)
    if query_dept:
        users = users.filter(PhongBan__icontains=query_dept)
    if query_status:
        status_val = True if query_status == 'Đang hoạt động' else False
        users = users.filter(TrangThai=status_val)

    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page_number)

    user_list = []
    for u in page_obj:
        user_list.append({
            'id': u.UserID,
            'username': u.username,
            'fullname': u.HoTen,
            'email': u.email,
            'phone': u.SoDienThoai,
            'dept': u.PhongBan,
            'role_id': u.VaiTroID.VaiTroID if u.VaiTroID else None,
            'role_name': u.VaiTroID.ChucVu if u.VaiTroID else '',
            'status': 'Đang hoạt động' if u.TrangThai else 'Vô hiệu hóa',
            'stt': u.SoThuTu
        })

    return JsonResponse({
        'status': 'success',
        'data': user_list,
        'pagination': {
            'total_count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page_obj.number,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
        }
    })


def api_upsert_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('id')

            if user_id:
                user = get_object_or_404(UserAccount, UserID=user_id)
            else:
                user = UserAccount()
                # Tự động gán STT
                max_stt = UserAccount.objects.aggregate(Max('SoThuTu'))['SoThuTu__max'] or 0
                user.SoThuTu = max_stt + 1

            user.username = data.get('username')
            user.HoTen = data.get('fullname')
            user.email = data.get('email')
            user.SoDienThoai = data.get('phone')
            user.PhongBan = data.get('dept')

            # Vai trò
            role_id = data.get('role_id')
            if role_id:
                user.VaiTroID = get_object_or_404(VaiTro, VaiTroID=role_id)

            # Trạng thái
            status_text = data.get('status')
            user.TrangThai = True if status_text == 'Đang hoạt động' else False

            # Mật khẩu (chỉ set nếu là tạo mới hoặc có nhập pass mới)
            password = data.get('password')
            if password:
                user.set_password(password)
            elif not user_id:
                # Nếu tạo mới mà ko nhập pass (mặc định cho demo)
                user.set_password('123456')

            user.save()
            return JsonResponse({'status': 'success', 'message': 'Lưu người dùng thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def api_delete_user(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('id')
            user = get_object_or_404(UserAccount, UserID=user_id)
            user.delete()
            return JsonResponse({'status': 'success', 'message': 'Xóa người dùng thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def api_vai_tro_list(request):
    roles = VaiTro.objects.all().order_by('ChucVu')
    role_list = [{'id': r.VaiTroID, 'name': r.ChucVu} for r in roles]
    return JsonResponse({'status': 'success', 'data': role_list})


# --- QUẢN LÝ ĐƠN VỊ ---
def quan_ly_don_vi_ben_ngoai(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    page_number = request.GET.get('page', 1)
    page_size = 5  # Giới hạn duy nhất cho quản lý đơn vị
    unit_id = request.GET.get('id')

    units = DonViBenNgoai.objects.all().order_by('SoThuTu', '-pk')

    if unit_id:
        units = units.filter(DonViNgoaiID=unit_id)
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
    unit_id = request.GET.get('id')

    units = DonViBenTrong.objects.all().order_by('SoThuTu', '-pk')

    if unit_id:
        units = units.filter(DonViTrongID=unit_id)
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

            if not unit.pk:
                # Tự động gán Số thứ tự (STT) lớn nhất + 1
                max_stt = model.objects.aggregate(Max('SoThuTu'))['SoThuTu__max'] or 0
                unit.SoThuTu = max_stt + 1

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
@login_required
def xu_ly_van_ban_index(request):
    query_so_ky_hieu = request.GET.get('so_ky_hieu', '')
    query_nguoi_xu_ly = request.GET.get('nguoi_xu_ly', '')
    query_ngay_nhan = request.GET.get('ngay_nhan', '')
    page_number = request.GET.get('page', 1)

    # Lấy danh sách văn bản và phân công liên quan
    documents = VanBanDen.objects.select_related('DonViNgoaiID', 'UserID').all().order_by('-NgayNhan')

    if query_so_ky_hieu:
        documents = documents.filter(SoKyHieu__icontains=query_so_ky_hieu)

    if query_nguoi_xu_ly and query_nguoi_xu_ly != '--- Chọn người xử lý ---':
        documents = documents.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly)

    if query_ngay_nhan:
        try:
            day, month, year = query_ngay_nhan.split('/')
            documents = documents.filter(NgayNhan__date=f"{year}-{month}-{day}")
        except:
            pass

    paginator = Paginator(documents, 10)
    page_obj = paginator.get_page(page_number)

    users = UserAccount.objects.all()
    units_trong = DonViBenTrong.objects.all()

    today = timezone.now().date()
    coming_soon_qs = PhanCong.objects.filter(
        HanXuLy__date__range=[today, today + timedelta(days=5)]
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID')

    overdue_qs_all = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành')

    overdue_count = overdue_qs_all.count()
    overdue_qs = overdue_qs_all.select_related('VanBanDenID').order_by('-HanXuLy')[:5]

    coming_soon_groups = {}
    for pc in coming_soon_qs:
        if pc.VanBanDenID:
            days = (pc.HanXuLy.date() - today).days
            days_str = "Hôm nay" if days == 0 else f"còn {days} ngày"
            if days_str not in coming_soon_groups:
                coming_soon_groups[days_str] = []
            coming_soon_groups[days_str].append(pc.VanBanDenID.SoKyHieu)

    overdue_groups = {}
    for pc in overdue_qs:
        if pc.VanBanDenID:
            days = (today - pc.HanXuLy.date()).days
            days_str = f"quá hạn {days} ngày"
            if days_str not in overdue_groups:
                overdue_groups[days_str] = []
            overdue_groups[days_str].append(pc.VanBanDenID.SoKyHieu)

    context = {
        'page_obj': page_obj,
        'users': users,
        'units_trong': units_trong,
        'query_so_ky_hieu': query_so_ky_hieu,
        'query_nguoi_xu_ly': query_nguoi_xu_ly,
        'query_ngay_nhan': query_ngay_nhan,
        'coming_soon_count': coming_soon_qs.count(),
        'overdue_count': overdue_count,
        'coming_soon_groups': coming_soon_groups,
        'overdue_groups': overdue_groups,
    }
    return render(request, 'xu_ly_van_ban/index.html', context)

@login_required
def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')

@login_required
def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')

@login_required
def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')

@login_required
def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')

@csrf_exempt
def api_phan_cong_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            user_id = data.get('user_id')
            han_xu_ly = data.get('han_xu_ly')
            ghi_chu = data.get('ghi_chu')

            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
            user = get_object_or_404(UserAccount, pk=user_id)

            phan_cong, created = PhanCong.objects.get_or_create(
                VanBanDenID=vb,
                defaults={'UserID': user, 'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu, 'TrangThaiXuLy': 'Đang xử lý'}
            )

            if not created:
                phan_cong.UserID = user
                phan_cong.HanXuLy = han_xu_ly
                phan_cong.GhiChu = ghi_chu
                phan_cong.save()

            vb.TrangThai = VanBanDen.TrangThaiChoices.DANG_XU_LY
            vb.save()

            return JsonResponse({'status': 'success', 'message': 'Phân công thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def api_cap_nhat_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            trang_thai_id = data.get('trang_thai')
            noi_dung = data.get('noi_dung')

            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
            phan_cong = PhanCong.objects.filter(VanBanDenID=vb).first()

            if not phan_cong:
                return JsonResponse({'status': 'error', 'message': 'Văn bản chưa được phân công!'}, status=400)

            old_status = phan_cong.TrangThaiXuLy
            new_status = 'Đang xử lý' if trang_thai_id == '1' else 'Hoàn thành'

            phan_cong.TrangThaiXuLy = new_status
            phan_cong.save()

            if new_status == 'Hoàn thành':
                vb.TrangThai = VanBanDen.TrangThaiChoices.HOAN_THANH
                vb.save()

            LichSuHoatDong.objects.create(
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                LoaiDoiTuong='VanBanDen',
                DoiTuongID=vb.VanBanDenID,
                HanhDong='Cập nhật trạng thái',
                NoiDungThayDoi=noi_dung,
                TrangThaiCu=old_status,
                TrangThaiMoi=new_status
            )

            return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def api_chuyen_tiep_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            don_vi_id = data.get('don_vi_id')
            noi_dung = data.get('noi_dung')

            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)

            ChuyenTiep.objects.create(
                VanBanDenID=vb,
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                NgayChuyenTiep=timezone.now(),
            )

            LichSuHoatDong.objects.create(
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                LoaiDoiTuong='VanBanDen',
                DoiTuongID=vb.VanBanDenID,
                HanhDong='Chuyển tiếp',
                NoiDungThayDoi=f"Chuyển tới đơn vị ID: {don_vi_id}. Nội dung: {noi_dung}"
            )

            return JsonResponse({'status': 'success', 'message': 'Chuyển tiếp thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@csrf_exempt
def api_bao_cao_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            loai_van_de = data.get('loai_van_de')
            mo_ta = data.get('mo_ta')

            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)

            BaoCao.objects.create(
                VanBanDenID=vb,
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                NgayBaoCao=timezone.now(),
                LoaiBaoCao=BaoCao.LoaiBaoCaoChoices.PHAN_HOI,
                GhiChu=f"[{loai_van_de}] {mo_ta}"
            )

            return JsonResponse({'status': 'success', 'message': 'Gửi báo cáo thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
