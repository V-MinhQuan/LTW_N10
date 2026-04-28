from .models import VanBanDi, PheDuyet, PhatHanh
import json
from datetime import timedelta

# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from .models import UserAccount
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max, Case, When, Value, IntegerField
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
from django.contrib import messages
from .forms import LoginForm
from .forms import VanBanDenForm
from .models import DonViBenTrong, UserAccount, VaiTro
from .models import PhanCong, ChuyenTiep, BaoCao, Butphe
from .models import VanBanDen, DonViBenNgoai, LichSuHoatDong
from .models import VanBanDi, PheDuyet, PhatHanh


# --- TRANG CHỦ ---
@login_required
def index(request):
    """View cho trang Dashboard - Hiển thị số liệu thực tế"""
    now = timezone.now()
    new_window = now - timedelta(days=7)

    # 1. Thống kê số liệu
    # Văn bản mới: Theo trạng thái 'MOI'
    count_new = VanBanDen.objects.filter(TrangThai='MOI').count()

    # Đang xử lý: Bao gồm cả trạng thái văn bản và các phân công đang thực hiện
    # Đếm các phân công có trạng thái 'Đang xử lý'
    count_processing = PhanCong.objects.filter(
        Q(TrangThaiXuLy='Đang xử lý') | Q(TrangThaiXuLy='DANG_XU_LY')
    ).count()

    # Quá hạn: Các phân công chưa hoàn thành và đã quá hạn
    count_overdue = PhanCong.objects.filter(
        HanXuLy__lt=now
    ).exclude(TrangThaiXuLy='Hoàn thành').count()

    # Hoàn thành: Chỉ đếm các văn bản hoàn thành trong 7 ngày qua
    count_completed = VanBanDen.objects.filter(
        TrangThai='HOAN_THANH',
        NgayHoanThanh__gte=now - timedelta(days=7)
    ).count()

    # 2. Văn bản đến mới nhất (Lấy 5 bản ghi)
    recent_documents = VanBanDen.objects.select_related('DonViNgoaiID').order_by('-NgayNhan')[:5]

    # 3. Công việc cần làm (Phân công cho user hiện tại)
    todo_list = PhanCong.objects.filter(
        UserID=request.user
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID').order_by('HanXuLy')[:5]

    context = {
        'count_new': count_new,
        'count_processing': count_processing,
        'count_overdue': count_overdue,
        'count_completed': count_completed,
        'recent_documents': recent_documents,
        'todo_list': todo_list,
    }
    return render(request, 'index.html', context)


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
    danh_sach = VanBanDen.objects.select_related('DonViNgoaiID', 'DonViTrongID').all().order_by('-VanBanDenID')
    don_vi_ngoai = DonViBenNgoai.objects.filter(trang_thai='ACTIVE')
    don_vi_trong = DonViBenTrong.objects.all()

    # Get filter params
    so_ky_hieu = request.GET.get('so_ky_hieu', '')
    trich_yeu = request.GET.get('trich_yeu', '')
    loai_vb = request.GET.get('loai_vb', '')
    don_vi_ngoai_id = request.GET.get('don_vi_ngoai', '')
    don_vi_trong_id = request.GET.get('don_vi_trong', '')
    ngay_tu = request.GET.get('ngay_tu', '')
    ngay_den = request.GET.get('ngay_den', '')
    trang_thai = request.GET.get('trang_thai', '')

    # Apply filters
    if so_ky_hieu:
        danh_sach = danh_sach.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        danh_sach = danh_sach.filter(TrichYeu__icontains=trich_yeu)
    if loai_vb:
        danh_sach = danh_sach.filter(LoaiVanBan__icontains=loai_vb)
    if don_vi_ngoai_id:
        danh_sach = danh_sach.filter(DonViNgoaiID_id=don_vi_ngoai_id)
    if don_vi_trong_id:
        danh_sach = danh_sach.filter(DonViTrongID_id=don_vi_trong_id)
    if ngay_tu:
        danh_sach = danh_sach.filter(NgayNhan__gte=ngay_tu)
    if ngay_den:
        danh_sach = danh_sach.filter(NgayNhan__lte=ngay_den)
    if trang_thai:
        if trang_thai == 'DANG_XU_LY':
            # "Đang xử lý" should include everything except "Hoàn thành" 
            # to match the frontend display logic
            danh_sach = danh_sach.exclude(TrangThai='HOAN_THANH')
        else:
            danh_sach = danh_sach.filter(TrangThai=trang_thai)

    from django.core.paginator import Paginator
    paginator = Paginator(danh_sach, 8) # Increased limit
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Build query string for pagination links
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
                error_msg = list(form.errors.values())[0][0] if form.errors else "Dữ liệu không hợp lệ."
                return JsonResponse({'status': 'error', 'message': error_msg})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'invalid method'})


def van_ban_den_xem(request, pk):
    from .models import PhanCong, ChuyenTiep, BaoCao
    vbd = VanBanDen.objects.select_related('DonViNgoaiID', 'DonViTrongID').filter(pk=pk).first()
    if not vbd:
        return JsonResponse({'status': 'error', 'message': 'Không tìm thấy'})

    qua_trinh_xu_ly = []
    # ... (existing logic for qua_trinh_xu_ly remains same)
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

    # 3. Lấy thông tin Báo cáo
    bao_caos = BaoCao.objects.filter(VanBanDenID=vbd, LoaiBaoCao='PHAN_HOI').select_related('UserID').order_by('NgayBaoCao')
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

    qua_trinh_xu_ly.sort(key=lambda x: x['time'] if x['time'] else timezone.now(), reverse=False)
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
            'don_vi_ngoai_ten': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Chưa xác định',
            'don_vi_ngoai_id': vbd.DonViNgoaiID_id,
            'don_vi_trong_ten': vbd.DonViTrongID.TenDonVi if vbd.DonViTrongID else 'Chưa xác định',
            'don_vi_trong_id': vbd.DonViTrongID_id,
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

        form = VanBanDenForm(request.POST, request.FILES, instance_id=pk)
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
            error_msg = list(form.errors.values())[0][0] if form.errors else "Dữ liệu không hợp lệ."
            return JsonResponse({'status': 'error', 'message': error_msg})
    return JsonResponse({'status': 'error'})


@csrf_exempt
def van_ban_den_xoa(request, pk):
    return JsonResponse({'status': 'error', 'message': 'Chức năng xóa văn bản đến đã bị vô hiệu hóa bởi quản trị viên.'})


def van_ban_den_lich_su(request):
    pk = request.GET.get('id')
    lich_su = LichSuHoatDong.objects.filter(LoaiDoiTuong='VanBanDen').select_related('UserID')
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
    trang_thai  = request.GET.get('trang_thai', '')
    page_number = request.GET.get('page', 1)
    page_size   = 8

    vbs = VanBanDi.objects.select_related('DonViNgoaiID', 'DonViTrongID', 'UserID').order_by('-VanBanDiID')
    if so_ky_hieu:
        vbs = vbs.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        vbs = vbs.filter(TrichYeu__icontains=trich_yeu)
    if loai_vb:
        vbs = vbs.filter(LoaiVanBan__icontains=loai_vb)
    if trang_thai:
        vbs = vbs.filter(TrangThai=trang_thai)
    if don_vi:
        vbs = vbs.filter(
            Q(DonViNgoaiID__TenDonVi__icontains=don_vi) |
            Q(DonViTrongID__TenDonVi__icontains=don_vi)
        )

    paginator  = Paginator(vbs, page_size)
    page_obj   = paginator.get_page(page_number)
    don_vi_ngoai_list = DonViBenNgoai.objects.filter(trang_thai='ACTIVE')
    don_vi_trong_list = DonViBenTrong.objects.all()
    # Lấy danh sách loại văn bản unique từ DB
    loai_vb_list = VanBanDi.objects.exclude(LoaiVanBan__isnull=True).exclude(LoaiVanBan='').values_list('LoaiVanBan', flat=True).distinct().order_by('LoaiVanBan')

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
        'loai_vb_list': loai_vb_list,
        'so_ky_hieu': so_ky_hieu,
        'trich_yeu': trich_yeu,
        'loai_vb': loai_vb,
        'don_vi': don_vi,
        'trang_thai': trang_thai,
    })

def api_vbdi_chi_tiet(request, pk):
    vb = get_object_or_404(VanBanDi, pk=pk)

    # Lấy lịch xử xử lý từ nhiều nguồn
    history = []

    # 1. Phân công
    for pc in PhanCong.objects.filter(VanBanDiID=vb).select_related('UserID'):
        history.append({
            'type': 'Phân công',
            'tag_class': 'vbd-process-tag-blue',
            'user': pc.UserID.HoTen if pc.UserID else 'N/A',
            'username': pc.UserID.username if pc.UserID else '',
            'action': f"Giao xử lý: {pc.GhiChu or ''}",
            'time': pc.NgayPhanCong
        })

    # 2. Chuyển tiếp
    for ct in ChuyenTiep.objects.filter(VanBanDiID=vb).select_related('UserID'):
        history.append({
            'type': 'Chuyển tiếp',
            'tag_class': 'vbd-process-tag-blue',
            'user': ct.UserID.HoTen if ct.UserID else 'N/A',
            'username': ct.UserID.username if ct.UserID else '',
            'action': "Chuyển xử lý văn bản",
            'time': ct.NgayChuyenTiep
        })

    # 3. Báo cáo / Phản hồi
    for bc in BaoCao.objects.filter(VanBanDiID=vb).select_related('UserID'):
        history.append({
            'type': 'Báo cáo',
            'tag_class': 'vbd-process-tag-gray',
            'user': bc.UserID.HoTen if bc.UserID else 'N/A',
            'username': bc.UserID.username if bc.UserID else '',
            'action': f"{bc.get_LoaiBaoCao_display()}: {bc.GhiChu or ''}",
            'time': bc.NgayBaoCao
        })

    # 4. Bút phê (Nếu cần)
    for bp in Butphe.objects.filter(VanBanDiID=vb).select_related('UserID'):
        history.append({
            'type': 'Bút phê',
            'tag_class': 'vbd-process-tag-green',
            'user': bp.UserID.HoTen if bp.UserID else 'N/A',
            'username': bp.UserID.username if bp.UserID else '',
            'action': bp.NoiDung or '',
            'time': bp.NgayButPhe
        })

    # Sắp xếp theo thời gian (giảm dần - mới nhất lên đầu)
    history.sort(key=lambda x: x['time'] if x['time'] else timezone.now(), reverse=True)

    # Format lại thời gian để trả về JSON
    for item in history:
        if item['time']:
            item['time'] = item['time'].strftime('%d/%m/%Y %H:%M')
        else:
            item['time'] = ''

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
            'xu_ly_history': history
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
        tt_map = {
            'DU_THAO': 'Dự thảo', 'CHO_PHE_DUYET': 'Chờ phê duyệt',
            'DA_PHE_DUYET': 'Đã phê duyệt', 'DA_PHAT_HANH': 'Đã phát hành',
        }
        # So sánh nội dung trước và sau
        changes = []
        new_so_ky_hieu = request.POST.get('so_ky_hieu', vb.SoKyHieu)
        new_trich_yeu  = request.POST.get('trich_yeu', vb.TrichYeu)
        new_loai_vb    = request.POST.get('loai_vb', vb.LoaiVanBan)
        new_trang_thai = request.POST.get('trang_thai')
        new_ngay       = request.POST.get('ngay_ban_hanh')
        new_ngoai_id   = request.POST.get('don_vi_ngoai_id')
        new_trong_id   = request.POST.get('don_vi_trong_id')

        # 1. So sánh các trường text
        if new_so_ky_hieu != (vb.SoKyHieu or ''):
            changes.append(f'Số ký hiệu: "{vb.SoKyHieu or "Trống"}" → "{new_so_ky_hieu}"')
        if new_trich_yeu != (vb.TrichYeu or ''):
            changes.append(f'Trích yếu: "{vb.TrichYeu or "Trống"}" → "{new_trich_yeu}"')
        if new_loai_vb != (vb.LoaiVanBan or ''):
            changes.append(f'Loại văn bản: "{vb.LoaiVanBan or "Trống"}" → "{new_loai_vb}"')

        # 2. So sánh trạng thái
        if new_trang_thai and new_trang_thai != cu:
            changes.append(f'Trạng thái: "{tt_map.get(cu, cu)}" → "{tt_map.get(new_trang_thai, new_trang_thai)}"')

        # 3. So sánh ngày
        old_ngay_str = vb.NgayBanHanh.strftime('%Y-%m-%d') if vb.NgayBanHanh else None
        if new_ngay and new_ngay != old_ngay_str:
            changes.append(f'Ngày ban hành: "{old_ngay_str or "Trống"}" → "{new_ngay}"')

        # 4. So sánh đơn vị
        if new_ngoai_id:
            new_ngoai_obj = DonViBenNgoai.objects.filter(pk=new_ngoai_id).first()
            old_ngoai_name = vb.DonViNgoaiID.TenDonVi if vb.DonViNgoaiID else 'Trống'
            if new_ngoai_obj and (not vb.DonViNgoaiID or vb.DonViNgoaiID.pk != new_ngoai_obj.pk):
                changes.append(f'Đơn vị ngoài: "{old_ngoai_name}" → "{new_ngoai_obj.TenDonVi}"')
                vb.DonViNgoaiID = new_ngoai_obj
        elif request.POST.get('don_vi_ngoai_id') == '' and vb.DonViNgoaiID:
             changes.append(f'Đơn vị ngoài: "{vb.DonViNgoaiID.TenDonVi}" → "Trống"')
             vb.DonViNgoaiID = None

        if new_trong_id:
            new_trong_obj = DonViBenTrong.objects.filter(pk=new_trong_id).first()
            old_trong_name = vb.DonViTrongID.TenDonVi if vb.DonViTrongID else 'Trống'
            if new_trong_obj and (not vb.DonViTrongID or vb.DonViTrongID.pk != new_trong_obj.pk):
                changes.append(f'Đơn vị trong: "{old_trong_name}" → "{new_trong_obj.TenDonVi}"')
                vb.DonViTrongID = new_trong_obj
        elif request.POST.get('don_vi_trong_id') == '' and vb.DonViTrongID:
             changes.append(f'Đơn vị trong: "{vb.DonViTrongID.TenDonVi}" → "Trống"')
             vb.DonViTrongID = None

        # Cập nhật các trường đã check
        vb.SoKyHieu   = new_so_ky_hieu
        vb.TrichYeu   = new_trich_yeu
        vb.LoaiVanBan = new_loai_vb
        if new_ngay: vb.NgayBanHanh = new_ngay
        if new_trang_thai: vb.TrangThai = new_trang_thai

        # 5. So sánh file
        if request.FILES.get('tep_dinh_kem'):
            vb.TepDinhKem = request.FILES['tep_dinh_kem']
            changes.append(f'Đã cập nhật tài liệu đính kèm: "{vb.TepDinhKem.name}"')
        elif request.POST.get('xoa_file') == '1':
            vb.TepDinhKem = None
            changes.append('Đã xóa tài liệu đính kèm')

        vb.save()
        noi_dung = 'Cập nhật: ' + '; '.join(changes) if changes else 'Lưu văn bản (không có thay đổi)'
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'CAP_NHAT', noi_dung, cu, vb.TrangThai)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

def api_vbdi_xoa(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb = get_object_or_404(VanBanDi, pk=pk)
        info = f'"{vb.TrichYeu or vb.SoKyHieu}"'
        # Log trước khi xóa
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'XOA', f'Đã xóa văn bản {info}', vb.TrangThai, 'DA_XOA')
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
        pd.ChuKySo        = data.get('chu_ky_so', '')
        pd.save()
        vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHE_DUYET if chap_nhan else VanBanDi.TrangThaiChoices.DU_THAO
        vb.save()
        ghi_chu_str = pd.GhiChu.strip() if pd.GhiChu else ''
        noi_dung = ('Phê duyệt văn bản' if chap_nhan
                    else 'Từ chối phê duyệt' + (f': {ghi_chu_str}' if ghi_chu_str else ''))
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'PHE_DUYET', noi_dung, cu, vb.TrangThai)
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
    vb = get_object_or_404(VanBanDi, pk=pk)
    lich_su = LichSuHoatDong.objects.filter(
        LoaiDoiTuong='VanBanDi', DoiTuongID=pk
    ).select_related('UserID').order_by('-ThoiGianCapNhat')
    tt_map = {
        'DU_THAO': 'Dự thảo', 'CHO_PHE_DUYET': 'Chờ phê duyệt',
        'DA_PHE_DUYET': 'Đã phê duyệt', 'DA_PHAT_HANH': 'Đã phát hành',
    }
    data = [{
        'thoi_gian': ls.ThoiGianCapNhat.strftime('%d/%m/%Y %H:%M'),
        'nguoi_thuc_hien': ls.UserID.HoTen if ls.UserID else 'Hệ thống',
        'ma_van_ban': vb.SoKyHieu,
        'trich_yeu': vb.TrichYeu or '',
        'noi_dung': ls.NoiDungThayDoi or '',
        'trang_thai_cu': tt_map.get(ls.TrangThaiCu or '', ls.TrangThaiCu or ''),
        'trang_thai_moi': tt_map.get(ls.TrangThaiMoi or '', ls.TrangThaiMoi or ''),
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

@login_required
def thong_tin_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        # Kiểm tra mật khẩu hiện tại
        if not request.user.check_password(old_password):
            messages.error(request, "Mật khẩu hiện tại không chính xác.")
            return render(request, 'quan_ly_nguoi_dung/thong_tin.html', {'open_modal': True})

        # Kiểm tra mật khẩu mới khớp nhau
        if new_password != confirm_password:
            messages.error(request, "Mật khẩu mới không khớp nhau.")
            return render(request, 'quan_ly_nguoi_dung/thong_tin.html', {'open_modal': True})

        # Cập nhật mật khẩu
        request.user.set_password(new_password)
        request.user.save()

        # Sau khi set_password, session sẽ bị logout, cần cập nhật lại session
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, request.user)

        messages.success(request, "Đổi mật khẩu thành công!")
        return redirect('thong_tin')

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

    # Sắp xếp: ACTIVE trước, INACTIVE sau
    users = UserAccount.objects.select_related('VaiTroID').all().order_by(
        Case(When(trang_thai='INACTIVE', then=1), default=0),
        'SoThuTu',
        'UserID'
    )

    if user_id:
        users = users.filter(UserID=user_id)
    if query_username:
        users = users.filter(username__icontains=query_username)
    if query_fullname:
        users = users.filter(HoTen__icontains=query_fullname)
    if query_dept:
        users = users.filter(PhongBan__icontains=query_dept)
    if query_status:
        # Map label lọc sang code DB
        status_db = 'ACTIVE' if query_status == 'Đang hoạt động' else 'INACTIVE'
        users = users.filter(trang_thai=status_db)

    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page_number)

    user_list = []
    for u in page_obj:
        # Chốt logic nhãn: ACTIVE -> Đang hoạt động, còn lại -> Vô hiệu hóa
        trang_thai_db = (u.trang_thai or 'ACTIVE').strip().upper()
        is_active = (trang_thai_db == 'ACTIVE')
        
        user_list.append({
            'id': u.UserID,
            'username': u.username,
            'fullname': u.HoTen,
            'email': u.email,
            'phone': u.SoDienThoai,
            'dept': u.PhongBan,
            'role_id': u.VaiTroID.VaiTroID if u.VaiTroID else None,
            'role_name': u.VaiTroID.ChucVu if u.VaiTroID else '',
            'status': trang_thai_db,
            'status_label': 'Đang hoạt động' if is_active else 'Vô hiệu hóa',
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
            status_code = data.get('status')
            if status_code in ['ACTIVE', 'INACTIVE']:
                user.trang_thai = status_code
            else:
                user.trang_thai = 'ACTIVE' if status_code == 'Đang hoạt động' else 'INACTIVE'

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


@csrf_exempt
def api_nguoi_dung_update_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('id')
            new_status = data.get('status') # 'ACTIVE' or 'INACTIVE'
            
            user = get_object_or_404(UserAccount, UserID=user_id)
            old_status = user.trang_thai
            user.trang_thai = new_status
            user.save()
            
            # Ghi lịch sử hoạt động
            action = 'Vô hiệu hóa' if new_status == 'INACTIVE' else 'Khôi phục'
            msg = f"{action} người dùng: {user.username}"
            LichSuHoatDong.objects.create(
                UserID=request.user,
                LoaiDoiTuong='UserAccount',
                DoiTuongID=user.UserID,
                HanhDong=action,
                NoiDungThayDoi=msg,
                TrangThaiCu=old_status,
                TrangThaiMoi=new_status
            )
            
            return JsonResponse({'status': 'success', 'message': f'Đã {action.lower()} người dùng thành công!'})
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
    query_status = request.GET.get('status', '') # Thêm filter trạng thái
    page_number = request.GET.get('page', 1)
    page_size = 5
    unit_id = request.GET.get('id')

    units = DonViBenNgoai.objects.annotate(
        sort_status=Case(
            When(trang_thai='INACTIVE', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('sort_status', 'SoThuTu', '-pk')

    if unit_id:
        units = units.filter(DonViNgoaiID=unit_id)
    if query_name:
        units = units.filter(TenDonVi__icontains=query_name)
    if query_address:
        units = units.filter(DiaChi__icontains=query_address)
    if query_contact:
        units = units.filter(NguoiLienHe__icontains=query_contact)
    if query_status and query_status != 'ALL':
        units = units.filter(trang_thai=query_status)

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
                'contact': u.NguoiLienHe,
                'status': u.trang_thai # Thêm status
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
        'query_contact': query_contact,
        'query_status': query_status
    })


def quan_ly_don_vi_ben_trong(request):
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    query_status = request.GET.get('status', 'ALL')
    page_number = request.GET.get('page', 1)
    page_size = 5  # Giới hạn duy nhất cho quản lý đơn vị
    unit_id = request.GET.get('id')

    units = DonViBenTrong.objects.annotate(
        sort_status=Case(
            When(trang_thai='INACTIVE', then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by('sort_status', 'SoThuTu', '-pk')

    if query_status == 'ACTIVE':
        units = units.filter(trang_thai='ACTIVE')
    elif query_status == 'INACTIVE':
        units = units.filter(trang_thai='INACTIVE')

    if unit_id:
        units = units.filter(DonViTrongID=unit_id)
    
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
                'contact': u.NguoiLienHe,
                'status': u.trang_thai
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
        'query_contact': query_contact,
        'query_status': query_status
    })


def api_don_vi_list(request):
    """Trả về danh sách đơn vị bên ngoài và bên trong để JS reload dynamic"""
    ngoai = [{'id': dv.DonViNgoaiID, 'ten': dv.TenDonVi} for dv in DonViBenNgoai.objects.all().order_by('TenDonVi')]
    trong = [{'id': dv.DonViTrongID, 'ten': dv.TenDonVi} for dv in DonViBenTrong.objects.all().order_by('TenDonVi')]
    return JsonResponse({'status': 'success', 'ngoai': ngoai, 'trong': trong})


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
    """API xử lý Ngừng hợp tác (Soft Delete) hoặc Xóa thực tế tùy loại"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit_type = data.get('type')
            unit_id = data.get('id')
            action = data.get('action') # 'deactivate' or 'reactivate' or 'delete'
            
            if unit_type == 'ngoai':
                unit = get_object_or_404(DonViBenNgoai, DonViNgoaiID=unit_id)
                if action == 'deactivate':
                    unit.trang_thai = 'INACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã chuyển sang ngừng hợp tác!'})
                elif action == 'reactivate':
                    unit.trang_thai = 'ACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã kích hoạt lại thành công!'})
                else:
                    # Giữ lại logic xóa cũ nếu cần cho các trường hợp khác, nhưng UI giờ dùng deactivate
                    unit.delete()
                    return JsonResponse({'status': 'success', 'message': 'Xóa thành công!'})
            else:
                unit = get_object_or_404(DonViBenTrong, DonViTrongID=unit_id)
                if action == 'deactivate':
                    unit.trang_thai = 'INACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã chuyển sang ngừng hợp tác!'})
                elif action == 'reactivate':
                    unit.trang_thai = 'ACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã kích hoạt lại thành công!'})
                else:
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
    
    # Lấy truy vấn cơ sở
    den_qs = VanBanDen.objects.select_related('DonViNgoaiID', 'UserID').all()
    di_qs = VanBanDi.objects.select_related('DonViNgoaiID', 'DonViTrongID', 'UserID').all()
    
    if query_so_ky_hieu:
        den_qs = den_qs.filter(SoKyHieu__icontains=query_so_ky_hieu)
        di_qs = di_qs.filter(SoKyHieu__icontains=query_so_ky_hieu)
    
    if query_nguoi_xu_ly and query_nguoi_xu_ly != '--- Chọn người xử lý ---':
        den_qs = den_qs.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly)
        di_qs = di_qs.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly)

    if query_ngay_nhan:
        try:
            day, month, year = query_ngay_nhan.split('/')
            den_qs = den_qs.filter(NgayNhan__date=f"{year}-{month}-{day}")
            di_qs = di_qs.filter(NgayBanHanh__date=f"{year}-{month}-{day}")
        except:
            pass

    # Phân loại để dùng trong template
    doc_list = []
    for doc in den_qs:
        doc.doc_type = 'den'
        doc.ngay_sort = doc.NgayNhan or timezone.now()
        doc_list.append(doc)
    for doc in di_qs:
        doc.doc_type = 'di'
        doc.ngay_sort = doc.NgayBanHanh or timezone.now()
        doc_list.append(doc)

    documents = sorted(doc_list, key=lambda x: x.ngay_sort, reverse=True)

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
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID', 'VanBanDiID')
    
    overdue_qs_all = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành')

    overdue_count = overdue_qs_all.count()
    overdue_qs = overdue_qs_all.select_related('VanBanDenID', 'VanBanDiID').order_by('-HanXuLy')[:5]

    # Nhóm theo số ngày
    coming_soon_groups = {}
    for pc in coming_soon_qs:
        doc_skh = pc.VanBanDenID.SoKyHieu if pc.VanBanDenID else (pc.VanBanDiID.SoKyHieu if pc.VanBanDiID else '')
        if doc_skh:
            days = (pc.HanXuLy.date() - today).days
            days_str = "Hôm nay" if days == 0 else f"còn {days} ngày"
            if days_str not in coming_soon_groups:
                coming_soon_groups[days_str] = []
            coming_soon_groups[days_str].append(doc_skh)

    overdue_groups = {}
    for pc in overdue_qs:
        doc_skh = pc.VanBanDenID.SoKyHieu if pc.VanBanDenID else (pc.VanBanDiID.SoKyHieu if pc.VanBanDiID else '')
        if doc_skh:
            days = (today - pc.HanXuLy.date()).days
            days_str = f"quá hạn {days} ngày"
            if days_str not in overdue_groups:
                overdue_groups[days_str] = []
            overdue_groups[days_str].append(doc_skh)

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

@login_required
@csrf_exempt
def api_phan_cong_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            user_id = data.get('user_id')
            han_xu_ly = data.get('han_xu_ly')
            ghi_chu = data.get('ghi_chu')
            doc_type = data.get('doc_type', 'den')

            # Kiểm tra nếu user_id rỗng
            if not user_id:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn ít nhất một người xử lý!'}, status=400)

            user_ids = user_id if isinstance(user_id, list) else [user_id]
            
            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDi'
                id_doituong = vb.VanBanDiID
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDen'
                id_doituong = vb.VanBanDenID

            for uid in user_ids:
                user = get_object_or_404(UserAccount, pk=uid)
                
                # Tạo hoặc cập nhật phân công
                if doc_type == 'di':
                    phan_cong, created = PhanCong.objects.get_or_create(
                        VanBanDiID=vb,
                        UserID=user,
                        defaults={'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu, 'TrangThaiXuLy': 'Đang xử lý'}
                    )
                else:
                    phan_cong, created = PhanCong.objects.get_or_create(
                        VanBanDenID=vb,
                        UserID=user,
                        defaults={'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu, 'TrangThaiXuLy': 'Đang xử lý'}
                    )

                if not created:
                    phan_cong.HanXuLy = han_xu_ly
                    phan_cong.GhiChu = ghi_chu
                    phan_cong.save()

            # Cập nhật trạng thái văn bản gốc
            if doc_type == 'di':
                vb.TrangThai = VanBanDi.TrangThaiChoices.CHO_PHE_DUYET
            else:
                vb.TrangThai = VanBanDen.TrangThaiChoices.DANG_XU_LY
            vb.save()

            # Ghi lịch sử hoạt động
            LichSuHoatDong.objects.create(
                UserID=request.user,
                LoaiDoiTuong=loai_doi_tuong,
                DoiTuongID=id_doituong,
                HanhDong='Phân công',
                NoiDungThayDoi=f"Phân công cho {len(user_ids)} người xử lý. Hạn: {han_xu_ly}"
            )

            return JsonResponse({'status': 'success', 'message': 'Phân công thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
@csrf_exempt
def api_cap_nhat_xlvb(request):
    if request.method == 'POST':
        try:
            # Dùng request.POST vì frontend gửi FormData
            so_ky_hieu = request.POST.get('so_ky_hieu')
            trang_thai_id = request.POST.get('trang_thai')
            noi_dung = request.POST.get('noi_dung')
            doc_type = request.POST.get('doc_type', 'den')
            tep_moi = request.FILES.get('tep_dinh_kem')

            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                phan_cong = PhanCong.objects.filter(VanBanDiID=vb).first()
                loai_doi_tuong = 'VanBanDi'
                id_doituong = vb.VanBanDiID
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                phan_cong = PhanCong.objects.filter(VanBanDenID=vb).first()
                loai_doi_tuong = 'VanBanDen'
                id_doituong = vb.VanBanDenID
            
            if not phan_cong:
                return JsonResponse({'status': 'error', 'message': 'Văn bản chưa được phân công!'}, status=400)
            
            old_status = phan_cong.TrangThaiXuLy
            new_status = 'Đang xử lý' if trang_thai_id == '1' else 'Hoàn thành'
            
            phan_cong.TrangThaiXuLy = new_status
            phan_cong.save()
            
            if new_status == 'Hoàn thành' and doc_type == 'den':
                vb.TrangThai = VanBanDen.TrangThaiChoices.HOAN_THANH
                vb.save()

            # Lưu tệp đính kèm mới nếu có
            if tep_moi:
                vb.TepDinhKem = tep_moi
                vb.save()
            
            # Ghi lịch sử
            msg_history = noi_dung
            if tep_moi:
                msg_history += f" (Đã cập nhật tệp: {tep_moi.name})"

            LichSuHoatDong.objects.create(
                UserID=request.user,
                LoaiDoiTuong=loai_doi_tuong,
                DoiTuongID=id_doituong,
                HanhDong='Cập nhật trạng thái',
                NoiDungThayDoi=msg_history,
                TrangThaiCu=old_status,
                TrangThaiMoi=new_status
            )
            
            return JsonResponse({'status': 'success', 'message': 'Cập nhật thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
@csrf_exempt
def api_chuyen_tiep_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            don_vi_id = data.get('don_vi_id') # d1, d2, ...
            noi_dung = data.get('noi_dung')
            doc_type = data.get('doc_type', 'den')

            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                ChuyenTiep.objects.create(VanBanDiID=vb, UserID=request.user, NgayChuyenTiep=timezone.now())
                LichSuHoatDong.objects.create(UserID=request.user, LoaiDoiTuong='VanBanDi', DoiTuongID=vb.VanBanDiID, HanhDong='Chuyển tiếp', NoiDungThayDoi=f"Chuyển tới đơn vị ID: {don_vi_id}. Nội dung: {noi_dung}")
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                ChuyenTiep.objects.create(VanBanDenID=vb, UserID=request.user, NgayChuyenTiep=timezone.now())
                LichSuHoatDong.objects.create(UserID=request.user, LoaiDoiTuong='VanBanDen', DoiTuongID=vb.VanBanDenID, HanhDong='Chuyển tiếp', NoiDungThayDoi=f"Chuyển tới đơn vị ID: {don_vi_id}. Nội dung: {noi_dung}")
            
            return JsonResponse({'status': 'success', 'message': 'Chuyển tiếp thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

@login_required
@csrf_exempt
def api_bao_cao_xlvb(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            loai_van_de = data.get('loai_van_de')
            mo_ta = data.get('mo_ta')
            doc_type = data.get('doc_type', 'den')

            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                BaoCao.objects.create(VanBanDiID=vb, UserID=request.user, NgayBaoCao=timezone.now(), LoaiBaoCao=BaoCao.LoaiBaoCaoChoices.PHAN_HOI, GhiChu=f"[{loai_van_de}] {mo_ta}")
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                BaoCao.objects.create(VanBanDenID=vb, UserID=request.user, NgayBaoCao=timezone.now(), LoaiBaoCao=BaoCao.LoaiBaoCaoChoices.PHAN_HOI, GhiChu=f"[{loai_van_de}] {mo_ta}")
            
            return JsonResponse({'status': 'success', 'message': 'Gửi báo cáo thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

