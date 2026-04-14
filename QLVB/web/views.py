from .models import VanBanDi, PheDuyet, PhatHanh
import json
from datetime import timedelta

# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from .models import UserAccount
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User # Hoặc model User của ông
from django.http import JsonResponse
from django.shortcuts import render

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


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)

            # --- LOGIC GHI NHỚ ĐĂNG NHẬP ---
            # 'remember_me' là cái 'name' của thẻ input checkbox trong HTML
            if request.POST.get('remember_me'):
                # Nếu có tích: lấy thời gian trong SESSION_COOKIE_AGE (ví dụ 1 ngày)
                request.session.set_expiry(None)
                print("Đã ghi nhớ đăng nhập")
            else:
                # Nếu không tích: hết hạn khi đóng trình duyệt (0)
                request.session.set_expiry(0)
                print("Không ghi nhớ - Thoát khi đóng trình duyệt")
            # -------------------------------

            return redirect('index')
        else:
            print(form.errors)
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

# --- QUÊN MẬT KHẨU ---
# 1. Gửi mã OTP
def api_send_otp(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if not email:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập email!'})

        try:
            # Kiểm tra email có tồn tại trong hệ thống không
            user = UserAccount.objects.get(email=email)

            # Tạo OTP 6 số
            otp = str(random.randint(100000, 999999))
            request.session['otp'] = otp
            request.session['reset_email'] = email

            # Gửi mail thực tế
            send_mail(
                'Mã xác thực Vietasia Travel',
                f'Mã OTP của bạn là: {otp}',
                'noreply@vietasia.com',
                [email],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success'})
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Email này không tồn tại trên hệ thống!'})
    return JsonResponse({'status': 'error'})


def api_confirm_reset(request):
    if request.method == 'POST':
        otp_input = request.POST.get('otp')
        new_pass = request.POST.get('new_password')
        otp_session = request.session.get('otp')
        email = request.session.get('reset_email')

        if otp_input == otp_session:
            user = UserAccount.objects.get(email=email)
            # Đổi mật khẩu trong Database (có mã hóa)
            user.password = make_password(new_pass)
            user.save()

            del request.session['otp']  # Xóa OTP sau khi dùng xong
            return JsonResponse({'status': 'success'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Mã OTP không đúng!'})

def quen_mat_khau_view(request):
    return render(request, 'login/quen_mat_khau.html')
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
    vbd = VanBanDen.objects.filter(pk=pk).first()
    if not vbd:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy'})
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
            'trang_thai': vbd.TrangThai
        }
    })


@csrf_exempt
def van_ban_den_sua(request, pk):
    if request.method == 'POST':
        vbd = VanBanDen.objects.filter(pk=pk).first()
        if not vbd:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy'})

        old_val = f"{vbd.SoKyHieu} - {vbd.TrichYeu}"

        form = VanBanDenForm(request.POST, request.FILES)
        if form.is_valid():
            vbd = form.save(user=request.user if request.user.is_authenticated else None, instance=vbd)

            LichSuHoatDong.objects.create(
                UserID=request.user if request.user.is_authenticated else None,
                LoaiDoiTuong='VanBanDen',
                DoiTuongID=vbd.VanBanDenID,
                HanhDong='Cập nhật',
                NoiDungThayDoi=f'Cập nhật từ {old_val} thành {vbd.SoKyHieu} - {vbd.TrichYeu}'
            )
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
        lich_su = lich_su.filter(DoiTuongID=pk)
    lich_su = lich_su.order_by('-ThoiGianCapNhat')

    data = []
    for ls in lich_su:
        data.append({
            'ThoiGianCapNhat': ls.ThoiGianCapNhat.strftime('%d/%m/%Y %H:%M') if ls.ThoiGianCapNhat else '',
            'NguoiThucHien': ls.UserID.HoTen if ls.UserID and ls.UserID.HoTen else (
                ls.UserID.username if ls.UserID else 'Hệ thống'),
            'HanhDong': ls.HanhDong,
            'NoiDungThayDoi': ls.NoiDungThayDoi
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
    return render(request, 'quan_ly_nguoi_dung/thong_tin.html')

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
def xu_ly_van_ban_index(request):
    query_so_ky_hieu = request.GET.get('so_ky_hieu', '')
    query_nguoi_xu_ly = request.GET.get('nguoi_xu_ly', '')
    query_ngay_nhan = request.GET.get('ngay_nhan', '')
    page_number = request.GET.get('page', 1)
    
    # Lấy danh sách văn bản và phân công liên quan
    # Ở đây chúng ta ưu tiên VanBanDen (Văn bản đến)
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

    # Phân trang
    paginator = Paginator(documents, 10)
    page_obj = paginator.get_page(page_number)
    
    # Dữ liệu bổ sung cho các dropdown
    users = UserAccount.objects.all()
    units_trong = DonViBenTrong.objects.all()
    
    # Thống kê cảnh báo chi tiết
    today = timezone.now().date()
    coming_soon_qs = PhanCong.objects.filter(
        HanXuLy__date__range=[today, today + timedelta(days=5)]
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID')
    
    overdue_qs_all = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành')
    
    overdue_count = overdue_qs_all.count()
    overdue_qs = overdue_qs_all.select_related('VanBanDenID').order_by('-HanXuLy')[:5]

    # Nhóm theo số ngày
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

    # Pagination context
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
            
            # Cập nhật hoặc tạo mới phân công
            phan_cong, created = PhanCong.objects.get_or_create(
                VanBanDenID=vb,
                defaults={'UserID': user, 'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu, 'TrangThaiXuLy': 'Đang xử lý'}
            )
            
            if not created:
                phan_cong.UserID = user
                phan_cong.HanXuLy = han_xu_ly
                phan_cong.GhiChu = ghi_chu
                phan_cong.save()
            
            # Cập nhật trạng thái văn bản
            vb.TrangThai = VanBanDen.TrangThaiChoices.DANG_XU_LY
            vb.save()
            
            return JsonResponse({'status': 'success', 'message': 'Phân công thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

def api_cap_nhat_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            trang_thai_id = data.get('trang_thai') # '1' hoặc '2'
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
            
            # Ghi lịch sử
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

def api_chuyen_tiep_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            don_vi_id = data.get('don_vi_id') # d1, d2, ...
            noi_dung = data.get('noi_dung')
            
            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
            
            # Ghi nhận chuyển tiếp
            ChuyenTiep.objects.create(
                VanBanDenID=vb,
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                NgayChuyenTiep=timezone.now(),
                # Thông tin khác có thể bổ sung nếu có model phù hợp
            )
            
            # Ghi lịch sử
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

def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')

def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')

def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')

def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')
