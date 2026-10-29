import os
import json
from datetime import timedelta
from itertools import chain
# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from .models import UserAccount
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max, Case, When, Value, IntegerField, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User  # Hoặc model User của ông
from django.http import JsonResponse
from django.shortcuts import render

# IMPORT CHO HỆ THỐNG THÔNG BÁO LỖI (MESSAGES)
from django.contrib import messages
from functools import wraps
from django.core.exceptions import PermissionDenied
from .forms import LoginForm
from django.views.decorators.cache import never_cache

from .forms import VanBanDenForm
from .models import DonViBenTrong, UserAccount, VaiTro
from .models import PhanCong, ChuyenTiep, BaoCao, Butphe, ThongBao
from .models import VanBanDen, DonViBenNgoai, LichSuHoatDong
from .models import VanBanDi, PheDuyet, PhatHanh

# ---HỆ THỐNG HELPER PHÂN QUYỀN---
def is_tgd(user):
    """Boss: Toàn quyền xem, nhưng không thao tác kỹ thuật/user"""
    if not user or not user.is_authenticated: return False
    # Giám đốc thật sự
    if user.VaiTroID and user.VaiTroID.ChucVu == 'Tổng giám đốc': return True
    # Superuser không phải Trưởng phòng ban khác và không phải Trưởng phòng IT
    if user.is_superuser and not user.is_department_head() and not user.is_it_head(): return True
    return False

def is_tp_it(user):
    """Admin kỹ thuật: Toàn quyền hệ thống & User"""
    if not user or not user.is_authenticated: return False
    # Trưởng phòng IT thật sự
    if user.VaiTroID and user.VaiTroID.ChucVu == 'Trưởng phòng IT': return True
    # Superuser không phải Trưởng phòng ban khác
    if user.is_superuser and not user.is_department_head(): return True
    return False

def is_truong_phong(user):
    """Quản lý phòng ban: Phân công, Duyệt trong phòng"""
    if not user or not user.is_authenticated: return False
    return user.VaiTroID and 'Trưởng phòng' in user.VaiTroID.ChucVu

def is_nhan_vien(user):
    """Nhân viên/Chuyên viên: Thực thi, cập nhật trạng thái cá nhân"""
    if not user or not user.is_authenticated: return False
    chuc_vu = user.VaiTroID.ChucVu if user.VaiTroID else ""
    return 'Nhân viên' in chuc_vu or 'Chuyên viên' in chuc_vu or 'CSKH' in chuc_vu

def permission_required(action, model=None):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            
            obj = None
            if model and 'pk' in kwargs:
                from django.shortcuts import get_object_or_404
                obj = get_object_or_404(model, pk=kwargs['pk'])
            
            # Kiểm tra quyền với tham số obj nếu có
            if request.user.can_perform_action(action, obj):
                return view_func(request, *args, **kwargs)
                
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.path.startswith('/api/'):
                return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền thực hiện hành động này.'}, status=403)
            return render(request, '403.html', status=403)
        return _wrapped_view
    return decorator


def get_filtered_documents(user, model_class):
    """Lọc dữ liệu văn bản dựa trên phạm vi chức vụ"""
    # 1. Tổng giám đốc: Xem toàn bộ công ty
    if is_tgd(user):
        return model_class.objects.all()

    # 2. Trưởng phòng: Xem văn bản của phòng mình
    if is_truong_phong(user):
        if model_class == VanBanDen:
            # Văn bản đến: Lọc theo phòng nhận HOẶC người xử lý thuộc phòng
            return model_class.objects.filter(
                Q(DonViTrongID=user.PhongBan) | 
                Q(UserID__PhongBan=user.PhongBan) |
                Q(phancong__UserID__PhongBan=user.PhongBan)
            ).distinct()
            
        # Mặc định cho Văn bản đi: Hiện cho phòng gửi, phòng xử lý HOẶC phòng nhận nội bộ
        return model_class.objects.filter(
            Q(NguoiGui__PhongBan=user.PhongBan) | 
            Q(UserID__PhongBan=user.PhongBan) | 
            Q(phancong__UserID__PhongBan=user.PhongBan) |
            Q(DonViTrongID__TenDonVi=user.PhongBan)
        ).distinct()

    # 3. Nhân viên: Chỉ xem văn bản mình soạn, hoặc được phân công/chuyển tiếp
    if model_class == VanBanDen:
        return model_class.objects.filter(
            Q(UserID=user) |
            Q(phancong__UserID=user) | 
            Q(chuyentiep__UserID=user)
        ).distinct()

    # Mặc định cho Văn bản đi: Loại bỏ Q(UserID=user) để tránh hiển thị văn bản cần phê duyệt trong danh sách chính
    return model_class.objects.filter(
        Q(NguoiGui=user) |
        Q(phancong__UserID=user) | 
        Q(chuyentiep__UserID=user)
    ).distinct()

def sync_van_ban_den(vb_di):
    """Đồng bộ trạng thái từ Văn bản đi sang Văn bản đến tương ứng"""
    from .models import VanBanDen
    from django.utils import timezone
    
    # Tìm hoặc tạo Văn bản đến tương ứng (dựa trên VanBanDiID và Người xử lý)
    # Tránh tạo trùng văn bản đến: kiểm tra theo SoKyHieu + UserID (Người xử lý phê duyệt)
    vbd = VanBanDen.objects.filter(VanBanDiID=vb_di, UserID=vb_di.UserID).first()
    
    if not vbd:
        vbd = VanBanDen(VanBanDiID=vb_di)
        vbd.NgayNhan = timezone.now()
        
    vbd.SoKyHieu = vb_di.SoKyHieu
    vbd.NgayBanHanh = vb_di.NgayBanHanh
    vbd.LoaiVanBan = vb_di.LoaiVanBan
    vbd.TrichYeu = vb_di.TrichYeu
    vbd.TrangThai = vb_di.TrangThai
    vbd.TepDinhKem = vb_di.TepDinhKem
    vbd.UserID = vb_di.UserID
    
    if vb_di.UserID and vb_di.UserID.PhongBan:
        vbd.DonViTrongID = vb_di.UserID.PhongBan
        
    # --- MỚI: Lưu phòng ban của người gửi phê duyệt vào Đơn vị gửi (Internal) ---
    if vb_di.NguoiGui and vb_di.NguoiGui.PhongBan:
        vbd.DonViGuiID = vb_di.NguoiGui.PhongBan
        vbd.DonViNgoaiID = None # Đảm bảo không bị trùng lặp với đơn vị ngoài
    # ----------------------------------------------------------------
        
    vbd.save()
    return vbd

# --- TÌM KIẾM TỔNG HỢP ---
@login_required
def tim_kiem_tong_hop(request):
    """Tìm kiếm văn bản đến và văn bản đi theo số ký hiệu hoặc trích yếu"""
    query = request.GET.get('q', '').strip()
    results_den = []
    results_di = []

    if query:
        user = request.user

        # --- Văn bản đến ---
        if is_tgd(user):
            den_qs = VanBanDen.objects.all()
        elif is_truong_phong(user):
            den_qs = VanBanDen.objects.filter(
                Q(DonViTrongID=user.PhongBan) |
                Q(UserID__PhongBan=user.PhongBan) |
                Q(phancong__UserID__PhongBan=user.PhongBan) |
                Q(chuyentiep__UserID__PhongBan=user.PhongBan)
            ).distinct()
        else:
            den_qs = VanBanDen.objects.filter(
                Q(UserID=user) |
                Q(phancong__UserID=user) |
                Q(chuyentiep__UserID=user)
            ).distinct()

        results_den = den_qs.filter(
            Q(SoKyHieu__icontains=query) | Q(TrichYeu__icontains=query)
        ).select_related('DonViNgoaiID', 'DonViTrongID').order_by('-NgayNhan')[:20]

        # --- Văn bản đi ---
        if is_tgd(user):
            di_qs = VanBanDi.objects.all()
        elif is_truong_phong(user):
            di_qs = VanBanDi.objects.filter(
                Q(NguoiGui__PhongBan=user.PhongBan) |
                Q(UserID__PhongBan=user.PhongBan) |
                Q(phancong__UserID__PhongBan=user.PhongBan)
            ).distinct()
        else:
            di_qs = VanBanDi.objects.filter(
                Q(NguoiGui=user) |
                Q(UserID=user) |
                Q(phancong__UserID=user) |
                Q(chuyentiep__UserID=user)
            ).distinct()

        results_di = di_qs.filter(
            Q(SoKyHieu__icontains=query) | Q(TrichYeu__icontains=query)
        ).select_related('DonViTrongID', 'DonViNgoaiID', 'NguoiGui').order_by('-NgayBanHanh')[:20]

    return render(request, 'tim_kiem.html', {
        'query': query,
        'results_den': results_den,
        'results_di': results_di,
        'total': len(results_den) + len(results_di),
    })

# --- TRANG CHỦ ---
@login_required
@never_cache
def index(request):
    """View cho trang Dashboard - Hiển thị số liệu thực tế"""
    now = timezone.now()
    # Thống kê dành cho quản lý cấp cao
    if is_tgd(request.user):
        count_new = VanBanDen.objects.filter(TrangThai='MOI').count()
        count_processing = PhanCong.objects.filter(Q(TrangThaiXuLy='Đang xử lý') | Q(TrangThaiXuLy='DANG_XU_LY')).count()
        count_overdue = PhanCong.objects.filter(HanXuLy__lt=now).exclude(TrangThaiXuLy='Hoàn thành').count()
        count_completed = VanBanDen.objects.filter(TrangThai='HOAN_THANH', NgayHoanThanh__gte=now - timedelta(days=7)).count()
    elif is_truong_phong(request.user):
        # Phạm vi văn bản của Trưởng phòng: khớp với những gì họ thấy trên trang Văn bản đến
        dept_docs = VanBanDen.objects.filter(
            Q(DonViTrongID=request.user.PhongBan) |
            Q(UserID__PhongBan=request.user.PhongBan) |
            Q(phancong__UserID__PhongBan=request.user.PhongBan) |
            Q(chuyentiep__UserID__PhongBan=request.user.PhongBan)
        ).distinct()
        count_new = dept_docs.filter(TrangThai='MOI').count()
        # Văn bản đang xử lý: loại trừ Hoàn thành và Chờ phê duyệt
        count_processing = dept_docs.exclude(
            TrangThai__in=['HOAN_THANH', 'CHO_PHE_DUYET']
        ).count()
        count_overdue = PhanCong.objects.filter(
            VanBanDenID__in=dept_docs, HanXuLy__lt=now
        ).exclude(TrangThaiXuLy='Hoàn thành').count()
        count_completed = dept_docs.filter(
            TrangThai='HOAN_THANH', NgayHoanThanh__gte=now - timedelta(days=7)
        ).count()
    else:
        # Thống kê cá nhân dành cho nhân viên
        count_new = VanBanDen.objects.filter(TrangThai='MOI', phancong__UserID=request.user).count()
        count_processing = PhanCong.objects.filter(UserID=request.user, TrangThaiXuLy__in=['Đang xử lý', 'DANG_XU_LY']).count()
        count_overdue = PhanCong.objects.filter(UserID=request.user, HanXuLy__lt=now).exclude(TrangThaiXuLy='Hoàn thành').count()
        count_completed = VanBanDen.objects.filter(TrangThai='HOAN_THANH', phancong__UserID=request.user, NgayHoanThanh__gte=now - timedelta(days=7)).count()

    # Văn bản đến mới nhất của người đang đăng nhập
    if is_tgd(request.user):
        # TGĐ và TP IT xem toàn bộ văn bản đến mới nhất
        recent_documents = VanBanDen.objects.select_related('DonViNgoaiID').order_by('-NgayNhan')[:5]
    elif is_truong_phong(request.user):
        # Trưởng phòng: chỉ văn bản đến thuộc phòng mình
        # Dùng subquery lấy ID trước để tránh trùng lặp do JOIN qua phancong
        dept_vbd_ids = VanBanDen.objects.filter(
            Q(DonViTrongID=request.user.PhongBan) |
            Q(UserID__PhongBan=request.user.PhongBan) |
            Q(phancong__UserID__PhongBan=request.user.PhongBan)
        ).values_list('VanBanDenID', flat=True).distinct()
        recent_documents = VanBanDen.objects.filter(
            VanBanDenID__in=dept_vbd_ids
        ).select_related('DonViNgoaiID').order_by('-NgayNhan')[:5]
    else:
        # Nhân viên: chỉ văn bản đến của chính mình
        # Dùng subquery lấy ID trước để tránh trùng lặp do JOIN qua phancong/chuyentiep
        nv_vbd_ids = VanBanDen.objects.filter(
            Q(UserID=request.user) |
            Q(phancong__UserID=request.user) |
            Q(chuyentiep__UserID=request.user)
        ).values_list('VanBanDenID', flat=True).distinct()
        recent_documents = VanBanDen.objects.filter(
            VanBanDenID__in=nv_vbd_ids
        ).select_related('DonViNgoaiID').order_by('-NgayNhan')[:5]

    # Công việc cần làm: quá hạn + sắp đến hạn (trong 7 ngày tới), lấy 3 cái gần nhất
    deadline_window = now + timedelta(days=7)
    todo_list = PhanCong.objects.filter(
        UserID=request.user,
        HanXuLy__lte=deadline_window,      # Hạn <= 7 ngày tới (bao gồm đã quá hạn)
    ).exclude(
        TrangThaiXuLy='Hoàn thành'         # Loại trừ đã hoàn thành
    ).select_related(
        'VanBanDenID', 'VanBanDiID'
    ).order_by('HanXuLy')[:3]              # Sắp xếp theo hạn gần nhất, lấy 3

    context = {
        'count_new': count_new,
        'count_processing': count_processing,
        'count_overdue': count_overdue,
        'count_completed': count_completed,
        'recent_documents': recent_documents,
        'todo_list': todo_list,
        'now': now,
    }
    return render(request, 'index.html', context)


@never_cache
def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            auth_login(request, user)
            if request.POST.get('remember_me'):
                request.session.set_expiry(None)
            else:
                request.session.set_expiry(0)
            return redirect('index')
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
@login_required
def van_ban_den_index(request):
    # CHÈN PHÂN QUYỀN[cite: 1]
    danh_sach = get_filtered_documents(request.user, VanBanDen).select_related('DonViNgoaiID', 'DonViTrongID', 'DonViGuiID', 'UserID').order_by('-VanBanDenID')
    don_vi_ngoai = DonViBenNgoai.objects.filter(trang_thai='ACTIVE')
    don_vi_trong = DonViBenTrong.objects.all()

    # Get filter params
    so_ky_hieu = request.GET.get('so_ky_hieu', '').strip()
    trich_yeu = request.GET.get('trich_yeu', '').strip()
    loai_vb = request.GET.get('loai_vb', '').strip()
    don_vi_ngoai_id = request.GET.get('don_vi_ngoai', '').strip()
    don_vi_trong_id = request.GET.get('don_vi_trong', '').strip()
    ngay_tu = request.GET.get('ngay_tu', '')
    ngay_den = request.GET.get('ngay_den', '')
    trang_thai = request.GET.get('trang_thai', '').strip()

    # Apply filters
    if so_ky_hieu:
        danh_sach = danh_sach.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        danh_sach = danh_sach.filter(TrichYeu__icontains=trich_yeu)
    if loai_vb:
        danh_sach = danh_sach.filter(LoaiVanBan__icontains=loai_vb)
    if don_vi_ngoai_id:
        if str(don_vi_ngoai_id).isdigit():
            danh_sach = danh_sach.filter(Q(DonViNgoaiID_id=don_vi_ngoai_id) | Q(DonViGuiID_id=don_vi_ngoai_id))
        else:
            danh_sach = danh_sach.filter(Q(DonViNgoaiID__TenDonVi__icontains=don_vi_ngoai_id) | Q(DonViGuiID__TenDonVi__icontains=don_vi_ngoai_id))
    if don_vi_trong_id:
        if str(don_vi_trong_id).isdigit():
            danh_sach = danh_sach.filter(DonViTrongID_id=don_vi_trong_id)
        else:
            danh_sach = danh_sach.filter(DonViTrongID__TenDonVi__icontains=don_vi_trong_id)
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
    paginator = Paginator(danh_sach, 8)  # Increased limit
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
        'don_vi_trong': don_vi_trong,
        'tong_so': paginator.count,
        'query_string': query_string
    })


@csrf_exempt
@login_required
@permission_required('them')
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


@login_required
@permission_required('xem', model=VanBanDen)
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
            'don_vi_ngoai_ten': vbd.DonViGuiID.TenDonVi if vbd.DonViGuiID else (vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Chưa xác định'),
            'don_vi_gui_trong_id': vbd.DonViGuiID_id,
            'don_vi_ngoai_id': vbd.DonViNgoaiID_id,
            'don_vi_trong_ten': vbd.DonViTrongID.TenDonVi if vbd.DonViTrongID else 'Chưa xác định',
            'don_vi_trong_id': vbd.DonViTrongID_id,
            'tep_dinh_kem': vbd.TepDinhKem.url if vbd.TepDinhKem else '',
            'tep_name': vbd.TepDinhKem.name.split('/')[-1] if vbd.TepDinhKem else '',
            'trang_thai': vbd.TrangThai,
            'tom_tat_ai': vbd.TomTatAI or '',
            'linh_vuc_ai': vbd.LinhVucAI or '',
            'qua_trinh_xu_ly': qua_trinh_xu_ly
        }
    })


@csrf_exempt
@login_required
@permission_required('sua', model=VanBanDen)
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
            'Đơn vị gửi': vbd.DonViGuiID.TenDonVi if vbd.DonViGuiID else (vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống'),
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
                'Đơn vị gửi': vbd.DonViGuiID.TenDonVi if vbd.DonViGuiID else (vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống'),
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
@login_required
@permission_required('xoa', model=VanBanDen)
def van_ban_den_xoa(request, pk):
    return JsonResponse(
        {'status': 'error', 'message': 'Chức năng xóa văn bản đến đã bị vô hiệu hóa bởi quản trị viên.'})


@login_required
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


# ==============================================================================
# AUTO-06: XỬ LÝ SỰ CỐ KẾT NỐI VÀ NGOẠI LỆ HỆ THỐNG (RETRY MECHANISM)
# ==============================================================================

def thuc_hien_thu_lai_ngoai_le(ngoai_le):
    """
    AUTO-06: Thực thi thử lại tác vụ bị gián đoạn do sự cố kết nối hoặc ngoại lệ
    """
    from web.models import NgoaiLeHeThong, ThongBao, UserAccount, VanBanDi
    from django.core.mail import EmailMessage
    from django.conf import settings
    from django.utils import timezone
    import os

    if ngoai_le.TrangThai in [NgoaiLeHeThong.TrangThaiChoices.THANH_CONG, NgoaiLeHeThong.TrangThaiChoices.DA_HUY]:
        return {'status': 'info', 'message': 'Tác vụ này đã hoàn tất hoặc đã được hủy.'}

    ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.DANG_THU_LAI
    ngoai_le.save()

    payload = ngoai_le.DuLieuPayload or {}

    try:
        if ngoai_le.LoaiNgoaiLe == NgoaiLeHeThong.LoaiNgoaiLeChoices.GUI_EMAIL:
            to_email = payload.get('to_email')
            if not to_email:
                raise ValueError("Không tìm thấy địa chỉ email người nhận trong dữ liệu hàng đợi.")

            subject = payload.get('subject') or "[Vietasia Travel] Phát hành văn bản"
            body = payload.get('body') or ""

            email = EmailMessage(
                subject=subject,
                body=body,
                from_email=getattr(settings, 'EMAIL_HOST_USER', 'lnnhatanh2018@gmail.com'),
                to=[to_email],
            )

            vb_id = payload.get('van_ban_di_id')
            if vb_id:
                try:
                    vb = VanBanDi.objects.get(pk=vb_id)
                    if vb.TepDinhKem and vb.TepDinhKem.storage.exists(vb.TepDinhKem.name):
                        file_content = vb.TepDinhKem.read()
                        file_name = os.path.basename(vb.TepDinhKem.name)
                        email.attach(file_name, file_content)
                except Exception as file_err:
                    print(f"Lỗi đính kèm file khi thử lại: {file_err}")

            email.send(fail_silently=False)

            # Thành công!
            ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.THANH_CONG
            ngoai_le.NgayThuLaiCuoi = timezone.now()
            ngoai_le.GhiChuKhacPhuc = f"Gửi email thành công tới {to_email} lúc {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}."
            ngoai_le.save()

            if ngoai_le.UserID:
                ThongBao.objects.create(
                    UserID=ngoai_le.UserID,
                    VanBanDiID=ngoai_le.VanBanDiID,
                    TieuDe="✅ Gửi email phát hành thành công sau khi kết nối lại",
                    NoiDung=f"Tác vụ gửi văn bản tới {to_email} đã được gửi thành công sau khi khôi phục mạng.",
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG
                )
            return {'status': 'success', 'message': f'Đã gửi lại email thành công tới {to_email}!'}

        elif ngoai_le.LoaiNgoaiLe == NgoaiLeHeThong.LoaiNgoaiLeChoices.DONG_BO_VAN_BAN:
            vb_id = payload.get('van_ban_di_id')
            if vb_id:
                vb = VanBanDi.objects.get(pk=vb_id)
                sync_van_ban_den(vb)
            ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.THANH_CONG
            ngoai_le.NgayThuLaiCuoi = timezone.now()
            ngoai_le.GhiChuKhacPhuc = f"Đồng bộ văn bản thành công lúc {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}."
            ngoai_le.save()
            return {'status': 'success', 'message': 'Đã đồng bộ văn bản thành công!'}

        else:
            ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.THANH_CONG
            ngoai_le.NgayThuLaiCuoi = timezone.now()
            ngoai_le.save()
            return {'status': 'success', 'message': 'Tác vụ đã được thực hiện thành công!'}

    except Exception as retry_err:
        ngoai_le.SoLanThuLai += 1
        ngoai_le.NgayThuLaiCuoi = timezone.now()
        ngoai_le.MoTaLoi = f"Thử lại lần {ngoai_le.SoLanThuLai} thất bại: {str(retry_err)}"

        if ngoai_le.SoLanThuLai >= ngoai_le.SoLanToiDa:
            ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.THAT_BAI
            admin_users = UserAccount.objects.filter(is_superuser=True) | UserAccount.objects.filter(VaiTroID__ChucVu__icontains='Admin')
            for adm in admin_users.distinct():
                ThongBao.objects.create(
                    UserID=adm,
                    VanBanDiID=ngoai_le.VanBanDiID,
                    TieuDe=f"🚨 Sự cố nghiêm trọng: Tác vụ #{ngoai_le.NgoaiLeID} thất bại tối đa",
                    NoiDung=f"Tác vụ '{ngoai_le.TieuDe}' đã thử lại {ngoai_le.SoLanToiDa} lần nhưng vẫn gặp lỗi ({str(retry_err)}). Cần kiểm tra kỹ thuật!",
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                    LienKet='/xu-ly-van-ban/?tab=ngoai_le'
                )
        else:
            ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.CHO_XU_LY

        ngoai_le.save()
        return {'status': 'error', 'message': f'Thử lại thất bại (Lần {ngoai_le.SoLanThuLai}/{ngoai_le.SoLanToiDa}): {str(retry_err)}'}


@login_required
def api_ngoai_le_danh_sach(request):
    """
    AUTO-06: Lấy danh sách sự cố ngoại lệ và hàng đợi thử lại
    """
    from web.models import NgoaiLeHeThong
    status_filter = request.GET.get('status')
    qs = NgoaiLeHeThong.objects.all().order_by('-NgayTao')
    if status_filter:
        qs = qs.filter(TrangThai=status_filter)

    pending_count = NgoaiLeHeThong.objects.filter(TrangThai__in=['CHO_XU_LY', 'THAT_BAI']).count()

    items = []
    for it in qs[:50]:
        items.append({
            'id': it.NgoaiLeID,
            'loai': it.LoaiNgoaiLe,
            'loai_display': it.get_LoaiNgoaiLe_display(),
            'tieu_de': it.TieuDe,
            'mo_ta_loi': it.MoTaLoi,
            'so_lan_thu_lai': it.SoLanThuLai,
            'so_lan_toi_da': it.SoLanToiDa,
            'trang_thai': it.TrangThai,
            'trang_thai_display': it.get_TrangThai_display(),
            'van_ban_di_id': it.VanBanDiID_id,
            'so_ky_hieu': it.VanBanDiID.SoKyHieu if it.VanBanDiID else (it.DuLieuPayload.get('so_ky_hieu') if it.DuLieuPayload else ''),
            'ngay_tao': it.NgayTao.strftime('%H:%M %d/%m/%Y'),
            'ngay_thu_lai_cuoi': it.NgayThuLaiCuoi.strftime('%H:%M %d/%m/%Y') if it.NgayThuLaiCuoi else None,
            'ghi_chu': it.GhiChuKhacPhuc or '',
        })

    return JsonResponse({
        'status': 'success',
        'pending_count': pending_count,
        'items': items
    })


@login_required
@csrf_exempt
def api_ngoai_le_thu_lai(request, pk):
    """
    AUTO-06: Kích hoạt thử lại thủ công một tác vụ ngoại lệ
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    from web.models import NgoaiLeHeThong
    ngoai_le = get_object_or_404(NgoaiLeHeThong, pk=pk)
    res = thuc_hien_thu_lai_ngoai_le(ngoai_le)
    return JsonResponse(res)


@login_required
@csrf_exempt
def api_ngoai_le_thu_lai_tat_ca(request):
    """
    AUTO-06: Thử lại tất cả các tác vụ đang chờ xử lý
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    from web.models import NgoaiLeHeThong
    pending = NgoaiLeHeThong.objects.filter(TrangThai=NgoaiLeHeThong.TrangThaiChoices.CHO_XU_LY)
    count = pending.count()
    success_count = 0
    for item in pending:
        res = thuc_hien_thu_lai_ngoai_le(item)
        if res.get('status') == 'success':
            success_count += 1
    return JsonResponse({
        'status': 'success',
        'message': f"Đã thử lại {count} tác vụ. Thành công: {success_count}/{count}."
    })


@login_required
@csrf_exempt
def api_ngoai_le_huy(request, pk):
    """
    AUTO-06: Hủy bỏ tác vụ ngoại lệ
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)
    from web.models import NgoaiLeHeThong
    from django.utils import timezone
    ngoai_le = get_object_or_404(NgoaiLeHeThong, pk=pk)
    ngoai_le.TrangThai = NgoaiLeHeThong.TrangThaiChoices.DA_HUY
    ngoai_le.GhiChuKhacPhuc = f"Đã hủy bởi {request.user.username} lúc {timezone.now().strftime('%d/%m/%Y %H:%M')}"
    ngoai_le.save()
    return JsonResponse({'status': 'success', 'message': 'Đã hủy tác vụ ngoại lệ thành công.'})


@login_required
@csrf_exempt
def api_vbd_chuyen_tiep_giam_doc(request, pk=None):
    """
    Chức năng chuyển tiếp văn bản đến lên cho role Giám đốc:
    - Tự động tìm kiếm tất cả tài khoản thuộc role Giám đốc
    - Tạo bản ghi ChuyenTiep cho từng Giám đốc
    - Gửi thông báo hệ thống (ThongBao) hiển thị trên Logo bar của Giám đốc
    - Ghi nhận lịch sử hoạt động của hệ thống
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ!'}, status=405)

    try:
        vbd_id = pk
        noi_dung = ''
        if request.content_type == 'application/json':
            import json
            data = json.loads(request.body)
            if not vbd_id:
                vbd_id = data.get('van_ban_den_id') or data.get('id')
            noi_dung = data.get('noi_dung', '').strip()
        else:
            if not vbd_id:
                vbd_id = request.POST.get('van_ban_den_id') or request.POST.get('id')
            noi_dung = request.POST.get('noi_dung', '').strip()

        if not vbd_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu ID văn bản đến!'}, status=400)

        vbd = get_object_or_404(VanBanDen, pk=vbd_id)

        # Kiểm tra quyền: Người dùng phải có quyền xem văn bản này
        if not request.user.can_perform_action('xem', vbd):
            return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền chuyển tiếp văn bản này!'}, status=403)

        # Lấy danh sách Giám đốc trong hệ thống
        giam_doc_list = list(UserAccount.objects.filter(
            Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
        ).exclude(VaiTroID__ChucVu__icontains='Trưởng phòng').distinct())

        if not giam_doc_list:
            return JsonResponse({'status': 'error', 'message': 'Hệ thống chưa thiết lập tài khoản vai trò Giám đốc!'}, status=400)

        now = timezone.now()
        gd_names = []
        noi_dung_chuyen = noi_dung or "Kính trình Giám đốc xem xét và cho ý kiến chỉ đạo."

        for gd in giam_doc_list:
            gd_names.append(gd.HoTen or gd.username)
            # Tạo bản ghi chuyển tiếp
            ChuyenTiep.objects.create(
                VanBanDenID=vbd,
                UserID=gd,
                NgayChuyenTiep=now
            )
            # Tạo thông báo chuông cho Giám đốc trên thanh Logo bar
            try:
                from web.models import ThongBao
                sender_name = request.user.HoTen or request.user.username
                sender_role = request.user.role_name or 'Người dùng'
                trich_yeu = vbd.TrichYeu or 'Không có trích yếu'
                ThongBao.objects.create(
                    UserID=gd,
                    VanBanDenID=vbd,
                    TieuDe=f"📨 [Chuyển tiếp] Văn bản đến {vbd.SoKyHieu}",
                    NoiDung=f"Đ/c {sender_name} ({sender_role}) đã chuyển tiếp văn bản đến '{vbd.SoKyHieu}' lên Giám đốc. Trích yếu: {trich_yeu}. Ý kiến trình: {noi_dung_chuyen}",
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                    LienKet=f"/xu-ly-van-ban/?so_ky_hieu={vbd.SoKyHieu}"
                )
            except Exception as notif_err:
                print(f"Lỗi tạo thông báo chuyển tiếp GD: {notif_err}")

        # Ghi lịch sử hoạt động
        LichSuHoatDong.objects.create(
            UserID=request.user,
            LoaiDoiTuong='VanBanDen',
            DoiTuongID=vbd.VanBanDenID,
            HanhDong='Chuyển tiếp',
            NoiDungThayDoi=f"Chuyển tiếp văn bản '{vbd.SoKyHieu}' lên Giám đốc ({', '.join(gd_names)}). Ý kiến trình: {noi_dung_chuyen}"
        )

        return JsonResponse({
            'status': 'success',
            'message': f"Đã chuyển tiếp văn bản '{vbd.SoKyHieu}' lên Giám đốc ({', '.join(gd_names)}) thành công!",
            'recipients': gd_names
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def api_vbd_thong_tin_xin_y_kien(request):
    """
    API cung cấp thông tin văn bản và xác định người nhận ý kiến theo phân cấp vai trò:
    - Nếu người gửi là Nhân viên: Gửi đến Trưởng phòng cùng phòng ban.
    - Nếu người gửi là Trưởng phòng: Chuyển văn bản đến Ban Giám đốc.
    """
    vbd_id = request.GET.get('vbd_id') or request.GET.get('id')
    if not vbd_id:
        return JsonResponse({'status': 'error', 'message': 'Thiếu ID văn bản!'}, status=400)

    vbd = get_object_or_404(VanBanDen, pk=vbd_id)
    user = request.user

    is_tp = user.is_department_head() or user.is_it_head()
    is_nv = user.is_nhan_vien() and not is_tp

    recipients_data = []
    target_type = ''
    target_type_label = ''

    if is_tp:
        target_type = 'GIAM_DOC'
        target_type_label = 'Ban Giám đốc'
        # Trưởng phòng chuyển lên Giám đốc
        gds = UserAccount.objects.filter(
            Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
        ).exclude(VaiTroID__ChucVu__icontains='Trưởng phòng').exclude(username='admin_temp').distinct()

        for gd in gds:
            recipients_data.append({
                'id': gd.UserID,
                'name': gd.HoTen or gd.username,
                'role': gd.role_name or 'Giám đốc',
                'dept': gd.PhongBan.TenDonVi if gd.PhongBan else 'Ban Giám đốc'
            })
    elif is_nv:
        target_type = 'TRUONG_PHONG'
        target_type_label = 'Trưởng phòng'
        # Nhân viên gửi đến Trưởng phòng cùng phòng ban
        tps = UserAccount.objects.filter(
            Q(PhongBan=user.PhongBan) | Q(VaiTroID__PhongBan=user.PhongBan)
        ).filter(
            Q(VaiTroID__ChucVu__startswith='Trưởng phòng') | Q(VaiTroID__ChucVu__icontains='Trưởng phòng')
        ).distinct()

        for tp in tps:
            recipients_data.append({
                'id': tp.UserID,
                'name': tp.HoTen or tp.username,
                'role': tp.role_name or 'Trưởng phòng',
                'dept': tp.PhongBan.TenDonVi if tp.PhongBan else (user.PhongBan.TenDonVi if user.PhongBan else '')
            })

        # Nếu phòng ban chưa có trưởng phòng, fallback sang Giám đốc
        if not recipients_data:
            target_type = 'GIAM_DOC'
            target_type_label = 'Ban Giám đốc (do phòng ban chưa có Trưởng phòng)'
            gds = UserAccount.objects.filter(
                Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
            ).exclude(VaiTroID__ChucVu__icontains='Trưởng phòng').exclude(username='admin_temp').distinct()
            for gd in gds:
                recipients_data.append({
                    'id': gd.UserID,
                    'name': gd.HoTen or gd.username,
                    'role': gd.role_name or 'Giám đốc',
                    'dept': gd.PhongBan.TenDonVi if gd.PhongBan else 'Ban Giám đốc'
                })
    else:
        target_type = 'GIAM_DOC'
        target_type_label = 'Ban Giám đốc'
        gds = UserAccount.objects.filter(
            Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
        ).exclude(UserID=user.UserID).exclude(username='admin_temp').distinct()
        for gd in gds:
            recipients_data.append({
                'id': gd.UserID,
                'name': gd.HoTen or gd.username,
                'role': gd.role_name or 'Giám đốc',
                'dept': gd.PhongBan.TenDonVi if gd.PhongBan else 'Ban Giám đốc'
            })

    return JsonResponse({
        'status': 'success',
        'data': {
            'vbd_id': vbd.VanBanDenID,
            'so_ky_hieu': vbd.SoKyHieu,
            'trich_yeu': vbd.TrichYeu or 'Không có trích yếu',
            'current_user': {
                'id': user.UserID,
                'name': user.HoTen or user.username,
                'role': user.role_name or 'Cán bộ',
                'dept': user.PhongBan.TenDonVi if user.PhongBan else ''
            },
            'target_type': target_type,
            'target_type_label': target_type_label,
            'recipients': recipients_data,
            'default_recipient': recipients_data[0] if recipients_data else None
        }
    })


@login_required
@csrf_exempt
def api_vbd_xin_y_kien(request):
    """
    Chức năng Xin ý kiến văn bản đến:
    - Nhân viên gửi lên Trưởng phòng cùng phòng ban.
    - Trưởng phòng chuyển tiếp lên Giám đốc.
    - Tự động tạo bản ghi BaoCao với LoaiBaoCao='XIN_Y_KIEN'
    - Cập nhật trạng thái văn bản sang CAN_XU_LY_LAI để kích hoạt luồng xử lý
    - Tạo ChuyenTiep và gửi thông báo chuông (ThongBao)
    - Ghi lịch sử hoạt động
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ!'}, status=405)

    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            vbd_id = data.get('van_ban_den_id') or data.get('id')
            recipient_id = data.get('recipient_id')
            ly_do = data.get('ly_do', '').strip()
            muc_do_khan = data.get('muc_do_khan', 'Bình thường')
        else:
            vbd_id = request.POST.get('van_ban_den_id') or request.POST.get('id')
            recipient_id = request.POST.get('recipient_id')
            ly_do = request.POST.get('ly_do', '').strip()
            muc_do_khan = request.POST.get('muc_do_khan', 'Bình thường')

        if not vbd_id:
            return JsonResponse({'status': 'error', 'message': 'Thiếu ID văn bản đến!'}, status=400)

        if not ly_do:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập lý do / nội dung xin ý kiến!'}, status=400)

        vbd = get_object_or_404(VanBanDen, pk=vbd_id)
        user = request.user

        # Xác định người nhận nếu client chưa truyền recipient_id
        if not recipient_id:
            is_tp = user.is_department_head() or user.is_it_head()
            is_nv = user.is_nhan_vien() and not is_tp
            if is_tp:
                gd = UserAccount.objects.filter(
                    Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
                ).exclude(VaiTroID__ChucVu__icontains='Trưởng phòng').exclude(username='admin_temp').first()
                if gd:
                    recipient_id = gd.UserID
            elif is_nv:
                tp = UserAccount.objects.filter(
                    Q(PhongBan=user.PhongBan) | Q(VaiTroID__PhongBan=user.PhongBan)
                ).filter(
                    Q(VaiTroID__ChucVu__startswith='Trưởng phòng') | Q(VaiTroID__ChucVu__icontains='Trưởng phòng')
                ).first()
                if tp:
                    recipient_id = tp.UserID

        if not recipient_id:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy người nhận ý kiến phù hợp!'}, status=400)

        recipient = get_object_or_404(UserAccount, pk=recipient_id)

        # Lưu trạng thái cũ và chuyển văn bản sang CAN_XU_LY_LAI để đưa vào danh sách cần xử lý
        trang_thai_cu = vbd.TrangThai
        vbd.TrangThai = 'CAN_XU_LY_LAI'
        vbd.save()

        now = timezone.now()

        # Tạo bản ghi BaoCao với LoaiBaoCao='XIN_Y_KIEN'
        report = BaoCao.objects.create(
            VanBanDenID=vbd,
            UserID=user,
            RecipientID=recipient,
            NgayBaoCao=now,
            LoaiBaoCao='XIN_Y_KIEN',
            GhiChu=ly_do[:250],
            TrangThai='CHUA_XEM',
            TrangThaiVBCu=trang_thai_cu
        )

        # Đảm bảo quyền truy cập cho người nhận
        ChuyenTiep.objects.create(
            VanBanDenID=vbd,
            UserID=recipient,
            NgayChuyenTiep=now,
            MucDoUuTien=muc_do_khan
        )

        # Gửi thông báo chuông (ThongBao) cho người nhận
        sender_dept = f" - {user.PhongBan.TenDonVi}" if user.PhongBan else ""
        ThongBao.objects.create(
            UserID=recipient,
            VanBanDenID=vbd,
            TieuDe=f"❓ [Xin ý kiến] Văn bản đến {vbd.SoKyHieu}",
            NoiDung=f"Đ/c {user.HoTen} ({user.role_name}{sender_dept}) xin ý kiến chỉ đạo về văn bản '{vbd.SoKyHieu}'. Lý do: {ly_do}",
            LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
            LienKet=f"/xu-ly-van-ban/?so_ky_hieu={vbd.SoKyHieu}"
        )

        # Ghi lịch sử hoạt động
        LichSuHoatDong.objects.create(
            UserID=user,
            LoaiDoiTuong='VanBanDen',
            DoiTuongID=vbd.VanBanDenID,
            HanhDong='Xin ý kiến',
            NoiDungThayDoi=f"Gửi xin ý kiến tới {recipient.HoTen} ({recipient.role_name}). Lý do: {ly_do}"
        )

        return JsonResponse({
            'status': 'success',
            'message': f"Đã gửi xin ý kiến văn bản '{vbd.SoKyHieu}' đến {recipient.HoTen} ({recipient.role_name}) thành công!",
            'recipient_name': recipient.HoTen,
            'recipient_role': recipient.role_name
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)



# --- QUẢN LÝ VĂN BẢN ĐI ---
@login_required
def van_ban_di_index(request):
    so_ky_hieu = request.GET.get('so_ky_hieu', '').strip()
    trich_yeu = request.GET.get('trich_yeu', '').strip()
    loai_vb = request.GET.get('loai_vb', '').strip()
    don_vi = request.GET.get('don_vi', '').strip()
    trang_thai = request.GET.get('trang_thai', '').strip()
    page_number = request.GET.get('page', 1)
    page_size = 8

    from django.db.models import Prefetch
    # ÁP DỤNG PHÂN QUYỀN LỌC DỮ LIỆU
    vbs = get_filtered_documents(request.user, VanBanDi).select_related('DonViNgoaiID', 'DonViTrongID', 'UserID').prefetch_related(
        Prefetch('phancong_set', queryset=PhanCong.objects.select_related('UserID').order_by('-NgayPhanCong'),
                 to_attr='ds_phan_cong')
    ).order_by('-VanBanDiID')
    don_vi_ngoai = request.GET.get('don_vi_ngoai', '').strip()
    don_vi_trong = request.GET.get('don_vi_trong', '').strip()
    ngay_tu = request.GET.get('ngay_tu', '')
    ngay_den = request.GET.get('ngay_den', '')

    if so_ky_hieu:
        vbs = vbs.filter(SoKyHieu__icontains=so_ky_hieu)
    if trich_yeu:
        vbs = vbs.filter(TrichYeu__icontains=trich_yeu)
    if loai_vb:
        vbs = vbs.filter(LoaiVanBan__icontains=loai_vb)
    if trang_thai:
        vbs = vbs.filter(TrangThai=trang_thai)
    
    if don_vi_ngoai:
        if str(don_vi_ngoai).isdigit():
            vbs = vbs.filter(DonViNgoaiID_id=don_vi_ngoai)
        else:
            vbs = vbs.filter(DonViNgoaiID__TenDonVi__icontains=don_vi_ngoai)
    if don_vi_trong:
        if str(don_vi_trong).isdigit():
            vbs = vbs.filter(DonViTrongID_id=don_vi_trong)
        else:
            vbs = vbs.filter(DonViTrongID__TenDonVi__icontains=don_vi_trong)
    if ngay_tu:
        vbs = vbs.filter(NgayBanHanh__gte=ngay_tu)
    if ngay_den:
        vbs = vbs.filter(NgayBanHanh__lte=ngay_den)

    paginator = Paginator(vbs, page_size)
    page_obj = paginator.get_page(page_number)
    don_vi_ngoai_list = DonViBenNgoai.objects.filter(trang_thai='ACTIVE')
    don_vi_trong_list = DonViBenTrong.objects.all()
    # Lấy danh sách loại văn bản unique từ DB
    loai_vb_list = VanBanDi.objects.exclude(LoaiVanBan__isnull=True).exclude(LoaiVanBan='').values_list('LoaiVanBan',
                                                                                                        flat=True).distinct().order_by(
        'LoaiVanBan')

    # Tính range trang hiển thị (tối đa 3 trang xung quanh trang hiện tại)
    current = page_obj.number
    total = paginator.num_pages
    start = max(current - 1, 1)
    end = min(start + 2, total)
    start = max(end - 2, 1)
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


@login_required
@permission_required('xem', model=VanBanDi)
def api_vbdi_chi_tiet(request, pk):
    vb = get_object_or_404(VanBanDi, pk=pk)

    # Lấy lịch xử xử lý từ nhiều nguồn
    history = []

    nguoi_xu_ly_list = []

    # 1. Phân công
    for pc in PhanCong.objects.filter(VanBanDiID=vb).select_related('UserID').order_by('NgayPhanCong'):
        if pc.UserID and pc.UserID.HoTen not in nguoi_xu_ly_list:
            nguoi_xu_ly_list.append(pc.UserID.HoTen)
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
            'action': f"{bc.LoaiBaoCao or 'Báo cáo'}: {bc.GhiChu or ''}",
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

    file_url = ''
    file_name = ''
    file_exists = False
    if vb.TepDinhKem:
        try:
            file_url = vb.TepDinhKem.url
            file_name = vb.TepDinhKem.name.split('/')[-1]
            file_exists = vb.TepDinhKem.storage.exists(vb.TepDinhKem.name)
        except Exception:
            file_url = f'/media/{vb.TepDinhKem}'
            file_name = str(vb.TepDinhKem).split('/')[-1]
            file_exists = False

    return JsonResponse({
        'status': 'success',
        'data': {
            'id': vb.VanBanDiID,
            'so_ky_hieu': vb.SoKyHieu,
            'trich_yeu': vb.TrichYeu or '',
            'loai_vb': vb.LoaiVanBan or '',
            'don_vi_ngoai': vb.DonViNgoaiID.TenDonVi if vb.DonViNgoaiID else '',
            'don_vi_ngoai_id': vb.DonViNgoaiID_id if vb.DonViNgoaiID else '',
            'don_vi_trong': 'Tất cả' if (vb.TrangThai == 'DA_PHAT_HANH' and not vb.DonViTrongID and not vb.DonViNgoaiID) else (vb.DonViTrongID.TenDonVi if vb.DonViTrongID else ''),
            'don_vi_trong_id': vb.DonViTrongID_id if vb.DonViTrongID else '',
            'don_vi_gui': vb.DonViGuiID.TenDonVi if vb.DonViGuiID else '',
            'don_vi_gui_id': vb.DonViGuiID_id if vb.DonViGuiID else '',
            'nguoi_soan': ", ".join(nguoi_xu_ly_list) if nguoi_xu_ly_list else (vb.UserID.HoTen if vb.UserID else ''),
            'nguoi_soan_id': vb.UserID_id if vb.UserID else '',
            'ngay_ban_hanh': vb.NgayBanHanh.strftime('%d/%m/%Y') if vb.NgayBanHanh else '',
            'trang_thai': vb.get_TrangThai_display(),
            'tep_dinh_kem': str(vb.TepDinhKem) if vb.TepDinhKem else '',
            'tep_dinh_kem_url': file_url,
            'tep_dinh_kem_name': file_name,
            'file_exists': file_exists,
            'tom_tat_ai': vb.TomTatAI or '',
            'linh_vuc_ai': vb.LinhVucAI or '',
            'xu_ly_history': history
        }
    })


@login_required
@permission_required('them', model=VanBanDi)
def api_vbdi_them_moi(request):

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        val_errors = validate_ho_so_van_ban(request.POST, request.FILES, loai='di', is_update=False, user=request.user)
        if val_errors:
            return JsonResponse({'status': 'error', 'message': ' \n'.join(val_errors)}, status=400)

        # Nhận cả form data lẫn file
        vb = VanBanDi()
        so_ky_hieu = request.POST.get('so_ky_hieu', '').strip()
        if so_ky_hieu and VanBanDi.objects.filter(SoKyHieu=so_ky_hieu).exists():
            return JsonResponse({'status': 'error', 'message': 'Số ký hiệu đã tồn tại trong hệ thống.'}, status=400)
            
        ngay_ban_hanh = request.POST.get('ngay_ban_hanh')
        if ngay_ban_hanh:
            from datetime import datetime
            from django.utils import timezone
            try:
                ngay_ban_hanh_date = datetime.strptime(ngay_ban_hanh, '%Y-%m-%d').date()
                if ngay_ban_hanh_date < timezone.now().date():
                    return JsonResponse({'status': 'error', 'message': 'Ngày ban hành phải lớn hơn hoặc bằng ngày hiện tại.'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Ngày ban hành không hợp lệ.'}, status=400)
        
        vb.SoKyHieu = so_ky_hieu
        vb.TrichYeu = request.POST.get('trich_yeu', '')
        vb.LoaiVanBan = request.POST.get('loai_vb', '')
        vb.NgayBanHanh = ngay_ban_hanh or None
        
        # Xử lý đơn vị: Ưu tiên chọn từ form, nếu không có thì lấy phòng ban của người tạo
        don_vi_trong_id = request.POST.get('don_vi_trong_id')
        don_vi_ngoai_id = request.POST.get('don_vi_ngoai_id')

        if don_vi_trong_id:
            if str(don_vi_trong_id).isdigit():
                vb.DonViTrongID = get_object_or_404(DonViBenTrong, pk=don_vi_trong_id)
            else:
                vb.DonViTrongID = DonViBenTrong.objects.filter(TenDonVi__iexact=don_vi_trong_id).first()
        if don_vi_ngoai_id:
            if str(don_vi_ngoai_id).isdigit():
                vb.DonViNgoaiID = get_object_or_404(DonViBenNgoai, pk=don_vi_ngoai_id)
            else:
                vb.DonViNgoaiID = DonViBenNgoai.objects.filter(TenDonVi__iexact=don_vi_ngoai_id).first()

        # Fallback nếu không chọn gì
        if not vb.DonViTrongID and not vb.DonViNgoaiID:
            if request.user.PhongBan:
                vb.DonViTrongID = request.user.PhongBan
            else:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn đơn vị nhận văn bản.'}, status=400)
            
        nguoi_soan_id = request.POST.get('nguoi_soan_id')
        if nguoi_soan_id:
            vb.UserID = get_object_or_404(UserAccount, pk=nguoi_soan_id)
        else:
            vb.UserID = request.user
            
        # Lưu người gửi (người tạo/người yêu cầu phê duyệt)
        vb.NguoiGui = request.user
        if request.user and hasattr(request.user, 'PhongBan'):
            vb.DonViGuiID = request.user.PhongBan
            
        if request.FILES.get('tep_dinh_kem'):
            vb.TepDinhKem = request.FILES['tep_dinh_kem']
        vb.TrangThai = request.POST.get('trang_thai', VanBanDi.TrangThaiChoices.DU_THAO)
        
        # Luồng mới: Nếu gửi phê duyệt
        if vb.TrangThai == VanBanDi.TrangThaiChoices.CHO_PHE_DUYET:
            vb.NgayGuiPheDuyet = timezone.now()
            vb.save()
            sync_van_ban_den(vb)
        else:
            vb.save()
            
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'THEM_MOI', 'Thêm mới văn bản', None, vb.TrangThai)
        return JsonResponse({'status': 'success', 'id': vb.VanBanDiID})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@permission_required('sua', model=VanBanDi)
def api_vbdi_cap_nhat(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        vb = get_object_or_404(VanBanDi, pk=pk)
        val_errors = validate_ho_so_van_ban(request.POST, request.FILES, loai='di', is_update=True, current_obj=vb, user=request.user)
        if val_errors:
            return JsonResponse({'status': 'error', 'message': ' \n'.join(val_errors)}, status=400)
        cu = vb.TrangThai
        tt_map = {
            'DU_THAO': 'Dự thảo', 'CHO_PHE_DUYET': 'Chờ phê duyệt',
            'DA_PHE_DUYET': 'Đã phê duyệt', 'DA_PHAT_HANH': 'Đã phát hành',
        }
        
        new_so_ky_hieu = request.POST.get('so_ky_hieu', '').strip()
        if not new_so_ky_hieu:
            new_so_ky_hieu = vb.SoKyHieu
            
        if new_so_ky_hieu and new_so_ky_hieu != vb.SoKyHieu:
            if VanBanDi.objects.filter(SoKyHieu=new_so_ky_hieu).exclude(pk=pk).exists():
                return JsonResponse({'status': 'error', 'message': 'Số ký hiệu đã tồn tại trong hệ thống.'}, status=400)
                
        new_ngay = request.POST.get('ngay_ban_hanh')
        if new_ngay and new_ngay != (vb.NgayBanHanh.strftime('%Y-%m-%d') if vb.NgayBanHanh else None):
            from datetime import datetime
            try:
                ngay_ban_hanh_date = datetime.strptime(new_ngay, '%Y-%m-%d').date()
                if ngay_ban_hanh_date < timezone.now().date():
                    return JsonResponse({'status': 'error', 'message': 'Ngày ban hành phải lớn hơn hoặc bằng ngày hiện tại.'}, status=400)
            except ValueError:
                return JsonResponse({'status': 'error', 'message': 'Ngày ban hành không hợp lệ.'}, status=400)

        # So sánh nội dung trước và sau
        changes = []
        new_trich_yeu = request.POST.get('trich_yeu', vb.TrichYeu)
        new_loai_vb = request.POST.get('loai_vb', vb.LoaiVanBan)
        new_trang_thai = request.POST.get('trang_thai')
        new_ngoai_id = request.POST.get('don_vi_ngoai_id')
        new_trong_id = request.POST.get('don_vi_trong_id')

        if not new_trong_id and not new_ngoai_id:
            return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn đơn vị nhận văn bản (trong hoặc ngoài).'}, status=400)

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
        new_ngoai_id = request.POST.get('don_vi_ngoai_id')

        if new_trong_id:
            if str(new_trong_id).isdigit():
                new_trong_obj = DonViBenTrong.objects.filter(pk=new_trong_id).first()
            else:
                new_trong_obj = DonViBenTrong.objects.filter(TenDonVi__iexact=new_trong_id).first()
            
            old_trong_name = vb.DonViTrongID.TenDonVi if vb.DonViTrongID else 'Trống'
            if new_trong_obj and (not vb.DonViTrongID or vb.DonViTrongID.pk != new_trong_obj.pk):
                changes.append(f'Đơn vị trong: "{old_trong_name}" → "{new_trong_obj.TenDonVi}"')
                vb.DonViTrongID = new_trong_obj
        elif request.POST.get('don_vi_trong_id') == '' and vb.DonViTrongID:
            changes.append(f'Đơn vị trong: "{vb.DonViTrongID.TenDonVi}" → "Trống"')
            vb.DonViTrongID = None

        if new_ngoai_id:
            if str(new_ngoai_id).isdigit():
                new_ngoai_obj = DonViBenNgoai.objects.filter(pk=new_ngoai_id).first()
            else:
                new_ngoai_obj = DonViBenNgoai.objects.filter(TenDonVi__iexact=new_ngoai_id).first()
                
            old_ngoai_name = vb.DonViNgoaiID.TenDonVi if vb.DonViNgoaiID else 'Trống'
            if new_ngoai_obj and (not vb.DonViNgoaiID or vb.DonViNgoaiID.pk != new_ngoai_obj.pk):
                changes.append(f'Đơn vị ngoài: "{old_ngoai_name}" → "{new_ngoai_obj.TenDonVi}"')
                vb.DonViNgoaiID = new_ngoai_obj
        elif request.POST.get('don_vi_ngoai_id') == '' and vb.DonViNgoaiID:
            changes.append(f'Đơn vị ngoài: "{vb.DonViNgoaiID.TenDonVi}" → "Trống"')
            vb.DonViNgoaiID = None

        # Cập nhật các trường đã check
        vb.SoKyHieu = new_so_ky_hieu
        vb.TrichYeu = new_trich_yeu
        vb.LoaiVanBan = new_loai_vb
        if new_ngay: vb.NgayBanHanh = new_ngay
        if new_trang_thai: 
            vb.TrangThai = new_trang_thai
            # Nếu chuyển sang chờ phê duyệt, ghi nhận người gửi
            if new_trang_thai == 'CHO_PHE_DUYET' and not vb.NguoiGui:
                vb.NguoiGui = request.user
        
        if request.user and hasattr(request.user, 'PhongBan'):
            vb.DonViGuiID = request.user.PhongBan
        
        vb.save()
        
        new_nguoi_soan_id = request.POST.get('nguoi_soan_id')
        if new_nguoi_soan_id:
            new_user = UserAccount.objects.filter(pk=new_nguoi_soan_id).first()
            if new_user and (not vb.UserID or vb.UserID.pk != new_user.pk):
                old_name = vb.UserID.HoTen if vb.UserID else 'Trống'
                changes.append(f'Người xử lý: "{old_name}" → "{new_user.HoTen}"')
                vb.UserID = new_user

        # 5. So sánh file
        if request.FILES.get('tep_dinh_kem'):
            vb.TepDinhKem = request.FILES['tep_dinh_kem']
            changes.append(f'Đã cập nhật tài liệu đính kèm: "{vb.TepDinhKem.name}"')
        elif request.POST.get('xoa_file') == '1':
            vb.TepDinhKem = None
            changes.append('Đã xóa tài liệu đính kèm')

        # Luồng mới: Nếu gửi phê duyệt
        if vb.TrangThai == VanBanDi.TrangThaiChoices.CHO_PHE_DUYET and cu != VanBanDi.TrangThaiChoices.CHO_PHE_DUYET:
            vb.NgayGuiPheDuyet = timezone.now()
            
        vb.save()
        
        if vb.TrangThai == VanBanDi.TrangThaiChoices.CHO_PHE_DUYET:
            sync_van_ban_den(vb)
            
        noi_dung = 'Cập nhật: ' + '; '.join(changes) if changes else 'Lưu văn bản (không có thay đổi)'
        _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'CAP_NHAT', noi_dung, cu, vb.TrangThai)
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@permission_required('xoa', model=VanBanDi)
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


@login_required
@permission_required('phe_duyet', model=VanBanDi)
def api_vbdi_phe_duyet(request, pk):
    """
    AUTO-02: Phê duyệt và ký văn bản điện tử 3 hành động:
    1. 'dong_y': Ký số & Phê duyệt -> Chuyển sang DA_PHE_DUYET
    2. 'yeu_cau_chinh_sua': Bắt buộc ghi chú -> Chuyển sang CAN_SUA_DOI, tự động thông báo
    3. 'tu_choi': Bắt buộc ghi chú lý do -> Chuyển sang DU_THAO, tự động thông báo
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        from django.db import transaction
        with transaction.atomic():
            vb = get_object_or_404(VanBanDi, pk=pk)
            
            if vb.TrangThai != VanBanDi.TrangThaiChoices.CHO_PHE_DUYET:
                return JsonResponse({'status': 'error', 'message': 'Văn bản không ở trạng thái chờ phê duyệt.'}, status=400)
                
            data = json.loads(request.body)
            cu = vb.TrangThai
            
            action = data.get('action')
            if not action:
                chap_nhan = data.get('chap_nhan', True)
                action = 'dong_y' if chap_nhan else 'tu_choi'
                
            ghi_chu = data.get('ghi_chu', '').strip()
            chu_ky_so = data.get('chu_ky_so', '').strip()
            
            from .models import PheDuyet, ThongBao
            
            pd = PheDuyet()
            pd.VanBanDiID = vb
            pd.UserID = request.user if request.user.is_authenticated else None
            pd.NgayPheDuyet = timezone.now()
            pd.GhiChu = ghi_chu
            pd.ChuKySo = chu_ky_so
            
            leader_name = request.user.HoTen or request.user.username if request.user.is_authenticated else 'Lãnh đạo'
            
            if action == 'dong_y':
                pd.TrangThaiDuyet = True
                vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHE_DUYET
                vb.NgayPheDuyet = timezone.now()
                noi_dung_ls = f"Phê duyệt văn bản {vb.SoKyHieu}."
                if ghi_chu:
                    noi_dung_ls += f" Ý kiến chỉ đạo: {ghi_chu}"
                thong_bao_tieu_de = f"Văn bản {vb.SoKyHieu} đã được phê duyệt"
                thong_bao_noi_dung = f"Giám đốc {leader_name} đã phê duyệt văn bản: '{vb.TrichYeu}'. Văn bản sẵn sàng phát hành."
                loai_tb = ThongBao.LoaiThongBaoChoices.HE_THONG
                success_msg = f"Phê duyệt văn bản {vb.SoKyHieu} thành công!"
                
            elif action == 'yeu_cau_chinh_sua':
                if not ghi_chu:
                    return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập nội dung yêu cầu chỉnh sửa vào ô Ghi chú.'}, status=400)
                pd.TrangThaiDuyet = False
                vb.TrangThai = VanBanDi.TrangThaiChoices.CAN_SUA_DOI
                noi_dung_ls = f"Yêu cầu chỉnh sửa văn bản {vb.SoKyHieu}. Lý do: {ghi_chu}"
                thong_bao_tieu_de = f"Yêu cầu chỉnh sửa văn bản: {vb.SoKyHieu}"
                thong_bao_noi_dung = f"Lãnh đạo {leader_name} yêu cầu chỉnh sửa văn bản '{vb.TrichYeu}'. Nội dung yêu cầu: {ghi_chu}"
                loai_tb = ThongBao.LoaiThongBaoChoices.NHAC_NHO
                success_msg = f"Đã gửi yêu cầu chỉnh sửa văn bản {vb.SoKyHieu} tới người soạn!"
                
            elif action == 'tu_choi':
                if not ghi_chu:
                    return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập lý do từ chối vào ô Ghi chú.'}, status=400)
                pd.TrangThaiDuyet = False
                vb.TrangThai = VanBanDi.TrangThaiChoices.DU_THAO
                noi_dung_ls = f"Từ chối phê duyệt văn bản {vb.SoKyHieu}. Lý do: {ghi_chu}"
                thong_bao_tieu_de = f"Văn bản {vb.SoKyHieu} bị từ chối phê duyệt"
                thong_bao_noi_dung = f"Lãnh đạo {leader_name} đã từ chối phê duyệt văn bản '{vb.TrichYeu}'. Lý do: {ghi_chu}"
                loai_tb = ThongBao.LoaiThongBaoChoices.NHAC_NHO
                success_msg = f"Đã từ chối phê duyệt văn bản {vb.SoKyHieu}!"
            else:
                return JsonResponse({'status': 'error', 'message': 'Hành động phê duyệt không hợp lệ.'}, status=400)
                
            pd.save()
            vb.save()
            
            # Đồng bộ sang văn bản đến
            sync_van_ban_den(vb)
            
            # TỰ ĐỘNG THÔNG BÁO CHO NGƯỜI SOẠN THẢO / NGƯỜI GỬI
            recipient_user = vb.UserID or vb.NguoiGui
            if recipient_user and recipient_user != request.user:
                ThongBao.objects.create(
                    UserID=recipient_user,
                    VanBanDiID=vb,
                    TieuDe=thong_bao_tieu_de,
                    NoiDung=thong_bao_noi_dung,
                    LoaiThongBao=loai_tb,
                    LienKet=f'/van-ban-di/?id={vb.VanBanDiID}'
                )
                
            _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'PHE_DUYET', noi_dung_ls, cu, vb.TrangThai)
            
            return JsonResponse({'status': 'success', 'message': success_msg, 'trang_thai': vb.TrangThai})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@permission_required('phat_hanh', model=VanBanDi)
def api_vbdi_phat_hanh(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    try:
        from django.db import transaction
        with transaction.atomic():
            vb = get_object_or_404(VanBanDi, pk=pk)
            
            # Kiểm tra trạng thái
            if vb.TrangThai != VanBanDi.TrangThaiChoices.DA_PHE_DUYET:
                return JsonResponse({'status': 'error', 'message': 'Văn bản chưa được phê duyệt.'}, status=400)

            data = json.loads(request.body)
            cu = vb.TrangThai
            
            ph_scope = data.get('ph_scope', 'internal')  # 'internal', 'external', 'both'
            don_vi_nhan_id = data.get('don_vi_trong_id')
            don_vi_ngoai_id = data.get('don_vi_ngoai_id')
            nguoi_nhan_id = data.get('nguoi_nhan_id')
            recipient_type = data.get('recipient_type', 'dept')
            
            ngay_ban_hanh_str = data.get('ngay_ban_hanh')
            if ngay_ban_hanh_str and ngay_ban_hanh_str != (vb.NgayBanHanh.strftime('%Y-%m-%d') if vb.NgayBanHanh else None):
                from datetime import datetime
                try:
                    ngay_ban_hanh_date = datetime.strptime(ngay_ban_hanh_str, '%Y-%m-%d').date()
                    if ngay_ban_hanh_date < timezone.now().date():
                        return JsonResponse({'status': 'error', 'message': 'Ngày ban hành phải lớn hơn hoặc bằng ngày hiện tại.'}, status=400)
                except ValueError:
                    return JsonResponse({'status': 'error', 'message': 'Ngày ban hành không hợp lệ.'}, status=400)
                    
            # 1. Lưu thông tin phát hành
            from .models import PhatHanh, DonViBenNgoai
            ph = PhatHanh()
            ph.VanBanDiID = vb
            ph.UserID = request.user if request.user.is_authenticated else None
            ph.TieuDe = data.get('trich_yeu', vb.TrichYeu)
            ph.NgayPhatHanh = data.get('ngay_ban_hanh') or timezone.now()
            ph.TrangThai = 'DA_PHAT_HANH'
            ph.save()
            
            vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHAT_HANH
            vb.NgayPhatHanh = data.get('ngay_ban_hanh') or timezone.now()
            if data.get('ngay_ban_hanh'):
                vb.NgayBanHanh = data.get('ngay_ban_hanh')
            else:
                vb.NgayBanHanh = timezone.now()
            
            if data.get('trich_yeu'):
                vb.TrichYeu = data.get('trich_yeu')

            # Xử lý đơn vị nhận nội bộ
            if ph_scope in ['internal', 'both']:
                if don_vi_nhan_id == 'all':
                    vb.DonViTrongID = None
                elif don_vi_nhan_id:
                    try:
                        vb.DonViTrongID_id = don_vi_nhan_id
                    except: pass
            else:
                vb.DonViTrongID = None

            # Xử lý đơn vị nhận bên ngoài
            don_vi_ngoai = None
            if ph_scope in ['external', 'both'] and don_vi_ngoai_id:
                try:
                    don_vi_ngoai = DonViBenNgoai.objects.get(pk=don_vi_ngoai_id)
                    vb.DonViNgoaiID = don_vi_ngoai
                except DonViBenNgoai.DoesNotExist:
                    pass

            vb.save()
            
            # 2. Đồng bộ sang Văn bản đến nếu có phát hành nội bộ
            if ph_scope in ['internal', 'both']:
                sync_van_ban_den(vb)

                dv_gui_trong = None
                if vb.NguoiGui and vb.NguoiGui.PhongBan:
                    dv_gui_trong = vb.NguoiGui.PhongBan

                from .models import VanBanDen
                vbd, created = VanBanDen.objects.get_or_create(
                    VanBanDiID=vb,
                    defaults={
                        'SoKyHieu': vb.SoKyHieu,
                        'TrichYeu': vb.TrichYeu,
                        'LoaiVanBan': vb.LoaiVanBan,
                        'NgayBanHanh': vb.NgayBanHanh,
                        'NgayNhan': timezone.now(),
                        'NgayVanBan': vb.NgayBanHanh,
                        'TepDinhKem': vb.TepDinhKem,
                        'TrangThai': 'DANG_XU_LY',
                        'DonViGuiID': dv_gui_trong
                    }
                )
                
                if not created:
                    vbd.SoKyHieu = vb.SoKyHieu
                    vbd.TrichYeu = vb.TrichYeu
                    vbd.LoaiVanBan = vb.LoaiVanBan
                    vbd.NgayBanHanh = vb.NgayBanHanh
                    vbd.TepDinhKem = vb.TepDinhKem
                    vbd.DonViGuiID = dv_gui_trong
                    vbd.DonViNgoaiID = None

                # Gán người nhận/đơn vị nhận cho Văn bản đến
                if don_vi_nhan_id == 'all':
                    vbd.DonViTrongID = None
                elif don_vi_nhan_id:
                    vbd.DonViTrongID_id = don_vi_nhan_id
                vbd.UserID = None
                vbd.save()

            # 3. GỬI FILE VĂN BẢN QUA EMAIL CHO ĐƠN VỊ BÊN NGOÀI
            email_msg_status = ""
            if ph_scope in ['external', 'both'] and don_vi_ngoai:
                if don_vi_ngoai.Email:
                    from django.core.mail import EmailMessage
                    from django.conf import settings
                    import os

                    subject = f"[Vietasia Travel] Phát hành văn bản: {vb.SoKyHieu} - {vb.TrichYeu}"
                    ban_hanh_str = vb.NgayBanHanh.strftime('%d/%m/%Y') if hasattr(vb.NgayBanHanh, 'strftime') else str(vb.NgayBanHanh)
                    body = f"""Kính gửi: {don_vi_ngoai.TenDonVi},
Người liên hệ: {don_vi_ngoai.NguoiLienHe or 'Quý đối tác'},

Công ty Du lịch Vietasia xin trân trọng thông báo phát hành văn bản chính thức đến Quý đơn vị với thông tin sau:
----------------------------------------------------------------------
- Số ký hiệu: {vb.SoKyHieu}
- Loại văn bản: {vb.LoaiVanBan or 'Công văn'}
- Ngày ban hành: {ban_hanh_str}
- Trích yếu nội dung: {vb.TrichYeu}
----------------------------------------------------------------------

Tệp văn bản chính thức được đính kèm trực tiếp theo thư này.
Kính đề nghị Quý đơn vị tiếp nhận và xử lý theo thẩm quyền.

Trân trọng cảm ơn sự phối hợp của Quý đơn vị!

---
CÔNG TY DU LỊCH VIETASIA
Email: {getattr(settings, 'EMAIL_HOST_USER', 'lnnhatanh2018@gmail.com')}
"""
                    email = EmailMessage(
                        subject=subject,
                        body=body,
                        from_email=getattr(settings, 'EMAIL_HOST_USER', 'lnnhatanh2018@gmail.com'),
                        to=[don_vi_ngoai.Email],
                    )

                    # Đính kèm file văn bản nếu có
                    if vb.TepDinhKem:
                        try:
                            if vb.TepDinhKem.storage.exists(vb.TepDinhKem.name):
                                file_content = vb.TepDinhKem.read()
                                file_name = os.path.basename(vb.TepDinhKem.name)
                                email.attach(file_name, file_content)
                        except Exception as attach_err:
                            print(f"Lỗi đính kèm file: {attach_err}")

                    try:
                        email.send(fail_silently=False)
                        email_msg_status = f" (Đã gửi email tệp văn bản thành công tới {don_vi_ngoai.Email})"
                    except Exception as mail_err:
                        import traceback
                        from web.models import NgoaiLeHeThong, ThongBao, UserAccount
                        print(f"Lỗi gửi email phát hành: {mail_err}")
                        
                        payload = {
                            'van_ban_di_id': vb.VanBanDiID,
                            'so_ky_hieu': vb.SoKyHieu,
                            'trich_yeu': vb.TrichYeu,
                            'don_vi_ngoai_id': don_vi_ngoai.DonViNgoaiID if don_vi_ngoai else None,
                            'ten_don_vi': don_vi_ngoai.TenDonVi if don_vi_ngoai else '',
                            'to_email': don_vi_ngoai.Email,
                            'subject': subject,
                            'body': body,
                            'tep_dinh_kem': vb.TepDinhKem.name if vb.TepDinhKem else None,
                        }
                        
                        ngoai_le = NgoaiLeHeThong.objects.create(
                            LoaiNgoaiLe=NgoaiLeHeThong.LoaiNgoaiLeChoices.GUI_EMAIL,
                            TieuDe=f"Gửi email phát hành {vb.SoKyHieu} tới {don_vi_ngoai.TenDonVi}",
                            MoTaLoi=str(mail_err),
                            ChiTietNgoaiLe=traceback.format_exc(),
                            DuLieuPayload=payload,
                            SoLanThuLai=0,
                            SoLanToiDa=3,
                            TrangThai=NgoaiLeHeThong.TrangThaiChoices.CHO_XU_LY,
                            VanBanDiID=vb,
                            UserID=request.user if request.user.is_authenticated else None
                        )
                        
                        # Gửi thông báo cho Quản trị viên
                        admin_users = UserAccount.objects.filter(is_superuser=True) | UserAccount.objects.filter(VaiTroID__ChucVu__icontains='Admin')
                        for adm in admin_users.distinct():
                            ThongBao.objects.create(
                                UserID=adm,
                                VanBanDiID=vb,
                                TieuDe=f"⚠️ Cảnh báo mất kết nối gửi mail {vb.SoKyHieu}",
                                NoiDung=f"Không thể gửi mail phát hành tới {don_vi_ngoai.Email} ({str(mail_err)}). Hệ thống đã tự động lưu vào hàng đợi thử lại #{ngoai_le.NgoaiLeID}.",
                                LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                                LienKet='/xu-ly-van-ban/?tab=ngoai_le'
                            )
                        
                        email_msg_status = f" (Sự cố kết nối khi gửi mail tới {don_vi_ngoai.Email}. Đã lưu vào hàng đợi tự động thử lại #{ngoai_le.NgoaiLeID})"
                else:
                    email_msg_status = f" (Đơn vị {don_vi_ngoai.TenDonVi} chưa có email cấu hình trong CSDL)"

            # 4. Ghi lịch sử hoạt động
            log_desc = f"Phát hành văn bản {vb.SoKyHieu}."
            if ph_scope == 'internal':
                log_desc += " Nơi nhận: Phòng ban nội bộ."
            elif ph_scope == 'external':
                log_desc += f" Nơi nhận: Đơn vị bên ngoài '{don_vi_ngoai.TenDonVi if don_vi_ngoai else ''}'{email_msg_status}."
            else:
                log_desc += f" Nơi nhận: Cả nội bộ và bên ngoài '{don_vi_ngoai.TenDonVi if don_vi_ngoai else ''}'{email_msg_status}."

            _ghi_lich_su(request, 'VanBanDi', vb.VanBanDiID, 'PHAT_HANH', log_desc, cu, vb.TrangThai)

            success_response_msg = f"Phát hành văn bản {vb.SoKyHieu} thành công!"
            if email_msg_status:
                success_response_msg += f"\n{email_msg_status.strip(' ()')}"

            return JsonResponse({
                'status': 'success',
                'message': success_response_msg
            })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
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

def validate_ho_so_van_ban(data, files, loai='di', is_update=False, current_obj=None, user=None):
    """
    AUTO-04: Tự động kiểm tra tính đầy đủ và hợp lệ của hồ sơ văn bản
    """
    errors = []
    so_ky_hieu = (data.get('so_ky_hieu') or '').strip()
    trich_yeu = (data.get('trich_yeu') or '').strip()
    loai_vb = (data.get('loai_vb') or '').strip()
    trang_thai = data.get('trang_thai', 'DU_THAO')
    
    # 1. Số ký hiệu
    if not so_ky_hieu:
        errors.append("Vui lòng nhập số ký hiệu văn bản.")
    else:
        qs = VanBanDi.objects.filter(SoKyHieu=so_ky_hieu)
        if is_update and current_obj:
            qs = qs.exclude(pk=current_obj.pk)
        if qs.exists():
            errors.append(f"Số ký hiệu '{so_ky_hieu}' đã tồn tại trong hệ thống. Vui lòng cấp số khác.")

    # 2. Trích yếu
    if not trich_yeu:
        errors.append("Vui lòng nhập trích yếu nội dung văn bản.")
    elif len(trich_yeu) < 5:
        errors.append("Trích yếu quá ngắn (tối thiểu 5 ký tự) để mô tả rõ nội dung văn bản.")

    # 3. Loại văn bản
    if not loai_vb:
        errors.append("Vui lòng chọn hoặc nhập loại văn bản.")

    # 4. Đơn vị nhận (phải có ít nhất đơn vị trong hoặc đơn vị ngoài)
    don_vi_trong = data.get('don_vi_trong_id')
    don_vi_ngoai = data.get('don_vi_ngoai_id')
    if not don_vi_trong and not don_vi_ngoai:
        if not (user and getattr(user, 'PhongBan', None)):
            errors.append("Hồ sơ chưa có đơn vị nhận văn bản. Vui lòng chọn phòng ban nội bộ hoặc đơn vị bên ngoài.")

    # 5. Tệp đính kèm & Điều kiện chuyển bước
    file_obj = files.get('tep_dinh_kem')
    existing_file = current_obj.TepDinhKem if current_obj else None
    has_file = bool(file_obj or existing_file)

    if trang_thai in ['CHO_PHE_DUYET', 'DA_PHAT_HANH'] and not has_file:
        errors.append("Hồ sơ văn bản bắt buộc phải có tệp tài liệu đính kèm (PDF, Word, Ảnh...) trước khi gửi phê duyệt hoặc phát hành.")

    if file_obj:
        MAX_SIZE = 25 * 1024 * 1024
        if file_obj.size > MAX_SIZE:
            errors.append(f"Tệp đính kèm '{file_obj.name}' ({file_obj.size // (1024*1024)}MB) vượt quá dung lượng tối đa 25MB.")
        import os
        ext = os.path.splitext(file_obj.name)[1].lower().lstrip('.')
        ALLOWED_EXTS = {'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg', 'zip', 'rar', 'txt'}
        if ext not in ALLOWED_EXTS:
            errors.append(f"Định dạng tệp '.{ext}' không được hỗ trợ. Vui lòng chỉ đính kèm tệp văn phòng (PDF, Word, Excel, Ảnh, ZIP).")

    # 6. Ngày ban hành
    ngay_ban_hanh = data.get('ngay_ban_hanh')
    if ngay_ban_hanh:
        from datetime import datetime
        try:
            if isinstance(ngay_ban_hanh, str):
                d = datetime.strptime(ngay_ban_hanh, '%Y-%m-%d').date()
            else:
                d = ngay_ban_hanh
            now_year = timezone.now().year
            if d.year < 2000 or d.year > now_year + 2:
                errors.append(f"Năm ban hành ({d.year}) ngoài phạm vi cho phép (2000 - {now_year + 2}).")
        except ValueError:
            errors.append("Ngày ban hành không đúng định dạng (YYYY-MM-DD).")

    return errors


@login_required
@login_required
def api_vbdi_tao_bieu_mau(request):
    """
    AUTO-03: Tự động sinh văn bản từ Biểu mẫu chuẩn (.docx)
    Áp dụng Nghị định 30/2020/NĐ-CP và thương hiệu Vietasia Travel
    """
    from web.docx_generator import generate_docx_template
    from django.http import FileResponse, HttpResponse
    import re
    import base64

    loai_vb = request.GET.get('loai_vb') or request.POST.get('loai_vb') or 'Công văn'
    so_ky_hieu = request.GET.get('so_ky_hieu') or request.POST.get('so_ky_hieu') or ''
    trich_yeu = request.GET.get('trich_yeu') or request.POST.get('trich_yeu') or 'Văn bản hành chính Vietasia Travel'
    don_vi = request.GET.get('don_vi') or request.POST.get('don_vi') or 'Quý Cơ quan / Đơn vị tiếp nhận'
    ngay_ban_hanh = request.GET.get('ngay_ban_hanh') or request.POST.get('ngay_ban_hanh') or None
    nguoi_ky = request.GET.get('nguoi_ky') or request.POST.get('nguoi_ky') or 'Đỗ Ngọc Hà'
    nguoi_soan = getattr(request.user, 'HoTen', None) or request.user.username or 'Cán bộ soạn thảo'

    stream = generate_docx_template(
        loai_vb=loai_vb,
        so_ky_hieu=so_ky_hieu or '.../CV-VAT-2026',
        trich_yeu=trich_yeu,
        don_vi_nhan=don_vi,
        nguoi_soan=nguoi_soan,
        nguoi_ky=nguoi_ky,
        ngay_ban_hanh=ngay_ban_hanh
    )

    clean_so = re.sub(r'[^a-zA-Z0-9_\-]', '_', so_ky_hieu) if so_ky_hieu else 'MauVanBan'
    clean_loai = re.sub(r'[^a-zA-Z0-9_\-]', '_', loai_vb)
    filename = f"{clean_so}_{clean_loai}.docx"

    if request.GET.get('format') == 'base64' or request.POST.get('format') == 'base64':
        content_bytes = stream.getvalue()
        b64_str = base64.b64encode(content_bytes).decode('ascii')
        return JsonResponse({
            'status': 'success',
            'filename': filename,
            'base64': b64_str,
            'size': len(content_bytes),
            'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })

    response = FileResponse(
        stream,
        as_attachment=True,
        filename=filename,
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )
    return response


def api_vbdi_goi_y_so_ky_hieu(request):
    """
    AUTO-05: Cấp số tự động theo quy tắc chuẩn công ty Vietasia Travel
    Cấu trúc chuẩn: [STT:3 chữ số]/[MÃ_LOẠI]-VAT-[NĂM]
    Ví dụ: 001/CV-VAT-2026, 002/QĐ-VAT-2026, 001/TTr-VAT-2026, 001/HĐ-VAT-2026
    """
    try:
        import re
        from django.utils import timezone
        
        loai_vb_input = (request.GET.get('loai_vb') or '').strip().lower()
        nam_param = request.GET.get('nam')
        try:
            nam = int(nam_param) if nam_param else timezone.now().year
        except ValueError:
            nam = timezone.now().year

        MAP_LOAI = {
            'công văn': 'CV', 'cong van': 'CV', 'cv': 'CV',
            'quyết định': 'QĐ', 'quyet dinh': 'QĐ', 'qd': 'QĐ', 'qđ': 'QĐ',
            'tờ trình': 'TTr', 'to trinh': 'TTr', 'ttr': 'TTr',
            'thông báo': 'TB', 'thong bao': 'TB', 'tb': 'TB',
            'báo cáo': 'BC', 'bao cao': 'BC', 'bc': 'BC',
            'hợp đồng': 'HĐ', 'hop dong': 'HĐ', 'hd': 'HĐ', 'hđ': 'HĐ',
            'kế hoạch': 'KH', 'ke hoach': 'KH', 'kh': 'KH',
            'biên bản': 'BB', 'bien ban': 'BB', 'bb': 'BB',
        }

        ma_loai = 'CV'
        for k, v in MAP_LOAI.items():
            if k in loai_vb_input:
                ma_loai = v
                break

        vbs = VanBanDi.objects.exclude(SoKyHieu__isnull=True).exclude(SoKyHieu='')
        max_seq = 0
        pat_new = re.compile(rf'^(\d+)/{re.escape(ma_loai)}-VAT-{nam}', re.IGNORECASE)
        pat_old_cv = re.compile(r'CV-DI-(\d+)', re.IGNORECASE)
        pat_generic = re.compile(r'^(\d+)/', re.IGNORECASE)

        for vb in vbs:
            skh = (vb.SoKyHieu or '').strip()
            m_new = pat_new.match(skh)
            if m_new:
                seq = int(m_new.group(1))
                if seq > max_seq:
                    max_seq = seq
                continue

            if ma_loai == 'CV':
                m_old = pat_old_cv.search(skh)
                if m_old:
                    seq = int(m_old.group(1))
                    if seq > max_seq:
                        max_seq = seq
                    continue

            m_gen = pat_generic.match(skh)
            if m_gen and (ma_loai in skh.upper()):
                seq = int(m_gen.group(1))
                if seq > max_seq:
                    max_seq = seq

        next_seq = max_seq + 1
        suffix = f"{ma_loai}-VAT-{nam}"
        suggested = f"{next_seq:03d}/{suffix}"
        
        # Đảm bảo duy nhất tuyệt đối
        while VanBanDi.objects.filter(SoKyHieu=suggested).exists():
            next_seq += 1
            suggested = f"{next_seq:03d}/{suffix}"

        return JsonResponse({
            'status': 'success',
            'suggested': suggested,
            'sequence': next_seq,
            'ma_loai': ma_loai,
            'loai_vb': loai_vb_input,
            'nam': nam
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


def _ghi_lich_su(request, loai, doi_tuong_id, hanh_dong, noi_dung, trang_thai_cu, trang_thai_moi):
    try:
        ls = LichSuHoatDong()
        ls.UserID = request.user if request.user.is_authenticated else None
        ls.LoaiDoiTuong = loai
        ls.DoiTuongID = doi_tuong_id
        ls.HanhDong = hanh_dong
        ls.NoiDungThayDoi = noi_dung
        ls.TrangThaiCu = trang_thai_cu
        ls.TrangThaiMoi = trang_thai_moi
        ls.save()
    except Exception:
        pass


# --- QUẢN LÝ NGƯỜI DÙNG ---
@login_required
@permission_required('quan_ly_nguoi_dung')
def quan_ly_nguoi_dung_index(request):

    user = request.user
    users = UserAccount.objects.all().select_related('VaiTroID').order_by('SoThuTu')
    return render(request, 'quan_ly_nguoi_dung/index.html', {
        'users': users,
        'can_edit': request.user.can_perform_action('quan_ly_nguoi_dung'),
        'total_users': users.count()
    })


@login_required
def thong_tin_view(request):
    user = request.user
    can_edit_all = user.is_giam_doc() or user.is_it_head()
    
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            ho_ten = request.POST.get('HoTen', '').strip()
            ngay_sinh = request.POST.get('NgaySinh', '').strip()
            gioi_tinh = request.POST.get('GioiTinh', '').strip()
            email = request.POST.get('email', '').strip()
            so_dien_thoai = request.POST.get('SoDienThoai', '').strip()

            # Kiểm tra không được để trống
            if not ho_ten or not ngay_sinh or not gioi_tinh or not email or not so_dien_thoai:
                messages.error(request, "Vui lòng nhập đầy đủ thông tin, không được để trống trường nào!")
                return redirect('thong_tin')

            # Cập nhật thông tin
            user.HoTen = ho_ten
            user.NgaySinh = ngay_sinh
            user.GioiTinh = gioi_tinh
            user.email = email
            user.SoDienThoai = so_dien_thoai
            
            user.save()
            messages.success(request, "Cập nhật thông tin thành công!")
            return redirect('thong_tin')


        elif action == 'change_password' or not action:  # Default or password
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

    return render(request, 'quan_ly_nguoi_dung/thong_tin.html', {'can_edit_all': can_edit_all})



# --- API NGƯỜI DÙNG ---
@login_required
def api_nguoi_dung_list(request):

    query_username = request.GET.get('username', '')
    query_fullname = request.GET.get('fullname', '')
    query_dept = request.GET.get('dept', '')
    query_status = request.GET.get('status', '')
    user_id = request.GET.get('id')
    page_number = request.GET.get('page', 1)
    page_size_param = request.GET.get('page_size', '5')

    if page_size_param == 'all':
        page_size = 999999
    else:
        try:
            page_size = int(page_size_param)
        except ValueError:
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
        if query_dept.isdigit():
            users = users.filter(PhongBan__pk=query_dept)
        else:
            users = users.filter(PhongBan__TenDonVi__icontains=query_dept)
    if query_status:
        # Map label lọc sang code DB
        status_db = 'ACTIVE' if query_status == 'Đang hoạt động' else 'INACTIVE'
        users = users.filter(trang_thai=status_db)

    paginator = Paginator(users, page_size)
    page_obj = paginator.get_page(page_number)

    user_list = []
    for u in page_obj:
        trang_thai_db = (u.trang_thai or 'ACTIVE').strip().upper()
        is_active = (trang_thai_db == 'ACTIVE')

        user_list.append({
            'id': u.UserID,
            'username': u.username,
            'fullname': u.HoTen,
            'email': u.email,
            'phone': u.SoDienThoai,
            'dept': str(u.PhongBan.TenDonVi) if u.PhongBan else '',
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


@csrf_exempt
@login_required
@permission_required('quan_ly_nguoi_dung')
def api_upsert_user(request):
    """Chốt chặn API: Dựa trên can_perform_action"""


    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_id = data.get('id')
            user = get_object_or_404(UserAccount, UserID=user_id) if user_id else UserAccount()

            if not user_id:  # Tạo mới
                max_stt = UserAccount.objects.aggregate(Max('SoThuTu'))['SoThuTu__max'] or 0
                user.SoThuTu = max_stt + 1
                user.set_password(data.get('password', '123456'))

            user.username = data.get('username')
            user.HoTen = data.get('fullname')
            user.email = data.get('email')
            user.PhongBan = data.get('dept')
            if data.get('role_id'):
                user.VaiTroID = get_object_or_404(VaiTro, pk=data.get('role_id'))
            new_status = data.get('status', 'ACTIVE')
            if new_status == 'INACTIVE' and user_id:
                from .models import PhanCong
                is_processing = PhanCong.objects.filter(UserID=user).exclude(TrangThaiXuLy='Hoàn thành').exists()
                if is_processing:
                    return JsonResponse({'status': 'error', 'message': 'Người dùng đang xử lý văn bản, không thể vô hiệu hóa'}, status=400)
            
            user.trang_thai = new_status
            user.save()
            msg = "Cập nhật người dùng thành công!" if user_id else "Thêm người dùng mới thành công!"
            return JsonResponse({'status': 'success', 'message': msg})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@csrf_exempt
@login_required
@permission_required('quan_ly_nguoi_dung')
def api_nguoi_dung_update_status(request):
    try:
        data = json.loads(request.body)
        user_id = data.get('id')
        new_status = data.get('status')
        u = get_object_or_404(UserAccount, pk=user_id)
        
        if new_status == 'INACTIVE':
            from .models import PhanCong
            # Kiểm tra xem người dùng có đang xử lý văn bản nào không
            is_processing = PhanCong.objects.filter(UserID=u).exclude(TrangThaiXuLy='Hoàn thành').exists()
            if is_processing:
                return JsonResponse({'status': 'error', 'message': 'Người dùng đang xử lý văn bản, không thể vô hiệu hóa'}, status=400)
        
        u.trang_thai = new_status
        u.save()
        msg = "Vô hiệu hóa người dùng thành công!" if new_status == 'INACTIVE' else "Kích hoạt lại người dùng thành công!"
        return JsonResponse({'status': 'success', 'message': msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def api_vai_tro_list(request):
    dept_name = request.GET.get('dept_name', '')
    roles = VaiTro.objects.all()
    if dept_name:
        roles = roles.filter(PhongBan__TenDonVi=dept_name)
    
    roles = roles.order_by('ChucVu')
    role_list = [{'id': r.VaiTroID, 'name': r.ChucVu} for r in roles]
    return JsonResponse({'status': 'success', 'data': role_list})


# --- QUẢN LÝ ĐƠN VỊ ---
@login_required
@permission_required('quan_ly_don_vi')
def quan_ly_don_vi_ben_ngoai(request):

    user = request.user
    query_name = request.GET.get('name', '')
    query_address = request.GET.get('address', '')
    query_contact = request.GET.get('contact', '')
    query_status = request.GET.get('status', '')  # Thêm filter trạng thái
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
                'status': u.trang_thai  # Thêm status
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
        'can_edit': request.user.can_perform_action('quan_ly_don_vi'),
        'query_name': query_name,
        'query_address': query_address,
        'query_contact': query_contact,
        'query_status': query_status
    })


@login_required
@permission_required('quan_ly_don_vi')
def quan_ly_don_vi_ben_trong(request):

    user = request.user
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
        'can_edit': request.user.can_perform_action('quan_ly_don_vi'),
        'query_name': query_name,
        'query_address': query_address,
        'query_contact': query_contact,
        'query_status': query_status
    })


@login_required
def api_don_vi_list(request):

    """Trả về danh sách đơn vị bên ngoài và bên trong để JS reload dynamic"""
    ngoai = [{'id': dv.DonViNgoaiID, 'ten': dv.TenDonVi} for dv in DonViBenNgoai.objects.all().order_by('TenDonVi')]
    trong = [{'id': dv.DonViTrongID, 'ten': dv.TenDonVi} for dv in DonViBenTrong.objects.all().order_by('TenDonVi')]
    return JsonResponse({'status': 'success', 'ngoai': ngoai, 'trong': trong})


@login_required
@csrf_exempt
@permission_required('quan_ly_don_vi')
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
                from django.db.models import Max
                max_stt = model.objects.aggregate(Max('SoThuTu'))['SoThuTu__max'] or 0
                unit.SoThuTu = max_stt + 1

            unit.save()
            return JsonResponse({'status': 'success', 'message': 'Lưu thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
@csrf_exempt
@permission_required('quan_ly_don_vi')
def api_delete_don_vi(request):

    """API xử lý Ngừng hợp tác (Soft Delete) hoặc Xóa thực tế tùy loại"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            unit_type = data.get('type')
            unit_id = data.get('id')
            action = data.get('action')  # 'deactivate' or 'reactivate' or 'delete'

            if unit_type == 'ngoai':
                unit = get_object_or_404(DonViBenNgoai, DonViNgoaiID=unit_id)
                if action in ['deactivate', 'delete']:
                    # Check if processing
                    is_processing = VanBanDen.objects.filter(DonViNgoaiID=unit, TrangThai__in=['MOI', 'DANG_XU_LY']).exists() or \
                                    VanBanDi.objects.filter(DonViNgoaiID=unit, TrangThai__in=['DU_THAO', 'CHO_PHE_DUYET', 'DA_PHE_DUYET']).exists()
                    if is_processing:
                        return JsonResponse({'status': 'error', 'message': 'Đơn vị bên ngoài đang xử lý công việc, không thể vô hiệu hóa'}, status=400)
                        
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
            else:
                unit = get_object_or_404(DonViBenTrong, DonViTrongID=unit_id)
                if action in ['deactivate', 'delete']:
                    # Check if processing
                    is_processing = VanBanDen.objects.filter(DonViTrongID=unit, TrangThai__in=['MOI', 'DANG_XU_LY']).exists() or \
                                    VanBanDi.objects.filter(DonViTrongID=unit, TrangThai__in=['DU_THAO', 'CHO_PHE_DUYET', 'DA_PHE_DUYET']).exists()
                    if is_processing:
                        return JsonResponse({'status': 'error', 'message': 'Đơn vị bên trong đang xử lý công việc, không thể vô hiệu hóa'}, status=400)
                        
                if action == 'deactivate':
                    unit.trang_thai = 'INACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã chuyển sang ngừng hoạt động!'})
                elif action == 'reactivate':
                    unit.trang_thai = 'ACTIVE'
                    unit.save()
                    return JsonResponse({'status': 'success', 'message': 'Đã kích hoạt hoạt động trở lại!'})
                else:
                    unit.delete()
                    return JsonResponse({'status': 'success', 'message': 'Xóa thành công!'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


# --- XỬ LÝ VĂN BẢN ĐIỀU HÀNH ---
@login_required
def xu_ly_van_ban_index(request):
    user = request.user
    # 1. Tự động cập nhật các văn bản đã quá thời hạn (cache 15 phút tránh UPDATE liên tục gây chậm DB)
    from django.core.cache import cache
    today = timezone.now().date()
    cache_key = f'update_overdue_tasks_{today}'
    if not cache.get(cache_key):
        PhanCong.objects.filter(
            HanXuLy__date__lt=today
        ).exclude(TrangThaiXuLy='Hoàn thành').exclude(TrangThaiXuLy='Quá hạn').update(TrangThaiXuLy='Quá hạn')
        cache.set(cache_key, True, timeout=900)

    # 2. Lấy tham số từ URL
    query_so_ky_hieu = request.GET.get('so_ky_hieu', '').strip()
    query_nguoi_xu_ly = request.GET.get('nguoi_xu_ly', '').strip()
    query_han_xu_ly = request.GET.get('han_xu_ly', '').strip()
    query_loai_xu_ly = request.GET.get('loai_xu_ly', '').strip()
    page_number = request.GET.get('page', 1)

    # 3. Khởi tạo QuerySet theo yêu cầu III
    # Văn bản đến (web_vanbanden)
    # Hiển thị nếu: UserID_id == request.user.UserID HOẶC DonViTrongID_id == request.user.PhongBan_id
    # Nếu là Tổng giám đốc hoặc Superuser (không phải TP phòng ban khác và không phải TP IT): Hiển thị tất cả
    if user.is_giam_doc() or (user.is_superuser and not user.is_department_head() and not user.is_it_head()):
        den_qs = VanBanDen.objects.all().select_related('DonViNgoaiID', 'DonViTrongID', 'DonViGuiID', 'UserID')
    else:
        # Loại trừ văn bản đến đang chờ phê duyệt/phát hành từ phía văn bản đi (tránh trùng lặp dòng trong trang xử lý)
        den_qs = VanBanDen.objects.filter(
            Q(UserID=user) | Q(DonViTrongID=user.PhongBan)
        ).exclude(
            VanBanDiID__TrangThai__in=['CHO_PHE_DUYET', 'DA_PHE_DUYET']
        ).select_related('DonViNgoaiID', 'DonViTrongID', 'DonViGuiID', 'UserID')

    # Văn bản đi cần xử lý (web_vanbandi)
    # Hiển thị nếu: request.user.UserID == web_vanbandi.UserID (NguoiXuLyPheDuyet_id)
    # HOẶC request.user.UserID == phancong__UserID (NguoiPhuTrachPhanCong_id)
    # Nếu là Tổng giám đốc hoặc Superuser (không phải TP phòng ban khác và không phải TP IT): Hiển thị tất cả văn bản đi cần xử lý
    if user.is_giam_doc() or (user.is_superuser and not user.is_department_head() and not user.is_it_head()):
        di_qs = VanBanDi.objects.all().select_related('DonViNgoaiID', 'DonViTrongID', 'UserID', 'NguoiGui').distinct()
    else:
        di_qs = VanBanDi.objects.filter(
            Q(UserID=user) | Q(phancong__UserID=user)
        ).select_related('DonViNgoaiID', 'DonViTrongID', 'UserID', 'NguoiGui').distinct()

    # 4. Áp dụng bộ lọc chung
    if query_so_ky_hieu:
        den_qs = den_qs.filter(SoKyHieu__icontains=query_so_ky_hieu)
        di_qs = di_qs.filter(SoKyHieu__icontains=query_so_ky_hieu)

    if query_nguoi_xu_ly and query_nguoi_xu_ly != '--- Chọn người xử lý ---':
        den_qs = den_qs.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly).distinct()
        di_qs = di_qs.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly).distinct()

    if query_han_xu_ly:
        den_qs = den_qs.filter(phancong__HanXuLy__date=query_han_xu_ly).distinct()
        di_qs = di_qs.filter(phancong__HanXuLy__date=query_han_xu_ly).distinct()

    # 5. LOGIC QUAN TRỌNG: Gộp danh sách và lọc theo dropdown
    doc_list = []
    now = timezone.now()

    # Lấy danh sách các yêu cầu Xin ý kiến đang chờ xử lý gửi đến người dùng hiện tại (hoặc tất cả nếu là TGĐ)
    if user.is_giam_doc():
        active_xin_y_kien = list(BaoCao.objects.filter(
            TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
        ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan', 'VanBanDenID', 'VanBanDiID').order_by('-NgayBaoCao'))
    elif user.is_department_head() or user.is_it_head():
        active_xin_y_kien = list(BaoCao.objects.filter(
            Q(RecipientID=user) | (Q(RecipientID__isnull=True) & Q(UserID__PhongBan=user.PhongBan)),
            TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
        ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan', 'VanBanDenID', 'VanBanDiID').order_by('-NgayBaoCao'))
    else:
        active_xin_y_kien = list(BaoCao.objects.filter(
            RecipientID=user,
            TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
        ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan', 'VanBanDenID', 'VanBanDiID').order_by('-NgayBaoCao'))

    xyk_den_map = {r.VanBanDenID_id: r for r in active_xin_y_kien if r.VanBanDenID_id}
    xyk_di_map = {r.VanBanDiID_id: r for r in active_xin_y_kien if r.VanBanDiID_id}

    # Bổ sung các văn bản đến đang được xin ý kiến nếu chưa có trong den_qs
    if query_loai_xu_ly in ['', 'den'] and xyk_den_map:
        missing_den_ids = [vid for vid in xyk_den_map.keys() if not den_qs.filter(pk=vid).exists()]
        if missing_den_ids:
            extra_den = VanBanDen.objects.filter(pk__in=missing_den_ids).select_related('DonViNgoaiID', 'DonViTrongID', 'DonViGuiID', 'UserID')
            den_qs = den_qs | extra_den

    # Prefetch tối ưu hoá sẵn UserID tránh N+1 query
    pc_prefetch = Prefetch('phancong_set', queryset=PhanCong.objects.select_related('UserID'))
    ct_prefetch = Prefetch('chuyentiep_set', queryset=ChuyenTiep.objects.select_related('UserID'))

    # Xử lý Văn bản đến (Chỉ add nếu chọn 'Tất cả' hoặc 'Văn bản đến')
    if query_loai_xu_ly in ['', 'den']:
        for doc in den_qs.prefetch_related(pc_prefetch, ct_prefetch):
            doc.doc_type = 'den'
            doc.ngay_sort = doc.NgayNhan or now
            pcs = list(doc.phancong_set.all())
            cts = list(doc.chuyentiep_set.all())
            doc.first_phancong = pcs[0] if pcs else None
            doc.last_chuyentiep = cts[-1] if cts else None

            # Kiểm tra trạng thái Xin ý kiến
            if doc.pk in xyk_den_map:
                r = xyk_den_map[doc.pk]
                doc.is_xin_y_kien = True
                doc.xin_y_kien_data = {
                    'report_id': r.PhanHoiID,
                    'nguoi_gui': r.UserID.HoTen or r.UserID.username,
                    'role_nguoi_gui': r.UserID.role_name or 'Cán bộ',
                    'phong_ban': r.UserID.PhongBan.TenDonVi if r.UserID.PhongBan else '',
                    'ly_do': r.GhiChu or '',
                    'ngay_gui': r.NgayBaoCao.strftime('%d/%m/%Y %H:%M') if r.NgayBaoCao else '',
                }
                doc.last_action_tag, doc.last_action_name = "tag-xin-y-kien", "Cần cho ý kiến"
            else:
                doc.is_xin_y_kien = False
                # Gán Tag màu
                if doc.TrangThai == 'CAN_XU_LY_LAI':
                    doc.last_action_tag, doc.last_action_name = "tag-bao-cao", "Đang báo cáo"
                else:
                    pc = doc.first_phancong
                    if not pc:
                        doc.last_action_tag, doc.last_action_name = "tag-phan-cong", "Phân công"
                    else:
                        if pc.TrangThaiXuLy == 'Hoàn thành':
                            doc.last_action_tag, doc.last_action_name = "tag-chuyen-tiep", "Chuyển tiếp"
                        elif pc.TrangThaiXuLy == 'Quá hạn':
                            doc.last_action_tag, doc.last_action_name = "tag-canh-bao", "Cảnh báo"
                        else:
                            doc.last_action_tag, doc.last_action_name = "tag-cap-nhat", "Cập nhật"
            doc_list.append(doc)

    # Xử lý Văn bản đi (Chỉ add nếu chọn 'Tất cả' hoặc 'Văn bản đi')
    if query_loai_xu_ly in ['', 'di']:
        # Văn bản đi cần xử lý hiển thị ở trang trung tâm nếu đang chờ duyệt hoặc đã duyệt
        di_tasks = di_qs.filter(
            TrangThai__in=[VanBanDi.TrangThaiChoices.CHO_PHE_DUYET, VanBanDi.TrangThaiChoices.DA_PHE_DUYET, VanBanDi.TrangThaiChoices.DA_PHAT_HANH]
        ).distinct()
        
        # Loại bỏ nếu người dùng chính là người đã thực hiện thao tác "Phát hành"
        # để danh sách "Xử lý" của họ không bị dồn ứ sau khi đã xong việc
        if not (is_tgd(user) or is_tp_it(user)):
            from .models import PhatHanh
            published_ids = PhatHanh.objects.filter(
                UserID=user,
                VanBanDiID__DonViTrongID__isnull=False
            ).values_list('VanBanDiID_id', flat=True)
            di_tasks = di_tasks.exclude(VanBanDiID__in=published_ids)

        for doc in di_tasks.prefetch_related(pc_prefetch, ct_prefetch):
            doc.doc_type = 'di'
            doc.ngay_sort = doc.NgayBanHanh or now
            pcs = list(doc.phancong_set.all())
            cts = list(doc.chuyentiep_set.all())
            doc.first_phancong = pcs[0] if pcs else None
            doc.last_chuyentiep = cts[-1] if cts else None

            # Kiểm tra trạng thái Xin ý kiến
            if doc.pk in xyk_di_map:
                r = xyk_di_map[doc.pk]
                doc.is_xin_y_kien = True
                doc.xin_y_kien_data = {
                    'report_id': r.PhanHoiID,
                    'nguoi_gui': r.UserID.HoTen or r.UserID.username,
                    'role_nguoi_gui': r.UserID.role_name or 'Cán bộ',
                    'phong_ban': r.UserID.PhongBan.TenDonVi if r.UserID.PhongBan else '',
                    'ly_do': r.GhiChu or '',
                    'ngay_gui': r.NgayBaoCao.strftime('%d/%m/%Y %H:%M') if r.NgayBaoCao else '',
                }
                doc.last_action_tag, doc.last_action_name = "tag-xin-y-kien", "Cần cho ý kiến"
            else:
                doc.is_xin_y_kien = False
                # Gán Tag màu
                if doc.TrangThai == 'CAN_XU_LY_LAI':
                    doc.last_action_tag, doc.last_action_name = "tag-bao-cao", "Đang báo cáo"
                else:
                    pc = doc.first_phancong
                    if not pc:
                        doc.last_action_tag, doc.last_action_name = "tag-phan-cong", "Phân công"
                    else:
                        if pc.TrangThaiXuLy == 'Hoàn thành':
                            doc.last_action_tag, doc.last_action_name = "tag-chuyen-tiep", "Chuyển tiếp"
                        elif pc.TrangThaiXuLy == 'Quá hạn':
                            doc.last_action_tag, doc.last_action_name = "tag-canh-bao", "Cảnh báo"
                        else:
                            doc.last_action_tag, doc.last_action_name = "tag-cap-nhat", "Cập nhật"
            doc_list.append(doc)

    # 6. Sắp xếp và Phân trang: Văn bản có Xin ý kiến (is_xin_y_kien) LUÔN đứng ở hàng đầu tiên (Top 1)
    documents = sorted(doc_list, key=lambda x: (1 if getattr(x, 'is_xin_y_kien', False) else 0, x.ngay_sort or now), reverse=True)
    paginator = Paginator(documents, 10)
    page_obj = paginator.get_page(page_number)

    # 7. Lấy dữ liệu Alert Box (Cảnh báo)
    danh_sach_nguoi_dung = UserAccount.objects.only('UserID', 'HoTen').all()
    coming_soon_list = list(PhanCong.objects.filter(
        UserID=user,
        HanXuLy__date__range=[today, today + timedelta(days=5)]
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID', 'VanBanDiID'))

    overdue_list_all = list(PhanCong.objects.filter(
        UserID=user,
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID', 'VanBanDiID'))

    coming_soon_groups = {}
    for pc in coming_soon_list:
        skh = pc.VanBanDenID.SoKyHieu if pc.VanBanDenID else (pc.VanBanDiID.SoKyHieu if pc.VanBanDiID else '')
        if skh:
            days = (pc.HanXuLy.date() - today).days
            coming_soon_groups.setdefault("Hôm nay" if days == 0 else f"còn {days} ngày", []).append(skh)

    overdue_groups = {}
    for pc in overdue_list_all[:10]:
        skh = pc.VanBanDenID.SoKyHieu if pc.VanBanDenID else (pc.VanBanDiID.SoKyHieu if pc.VanBanDiID else '')
        if skh:
            days = (today - pc.HanXuLy.date()).days
            overdue_groups.setdefault(f"quá hạn {days} ngày", []).append(skh)

    # Lấy số lượng báo cáo chưa xử lý gửi cho mình
    if is_tgd(user):
        report_count = BaoCao.objects.filter(TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']).count()
    else:
        report_count = BaoCao.objects.filter(RecipientID=user, TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']).count()

    # 8. Context
    from .models import DonViBenTrong, DonViBenNgoai
    context = {
        'page_obj': page_obj,
        'danh_sach_nguoi_dung': danh_sach_nguoi_dung,
        'don_vi_trong_list': DonViBenTrong.objects.all().order_by('SoThuTu'),
        'don_vi_ngoai_list': DonViBenNgoai.objects.filter(trang_thai='ACTIVE').order_by('TenDonVi'),
        'query_so_ky_hieu': query_so_ky_hieu,
        'query_nguoi_xu_ly': query_nguoi_xu_ly,
        'query_han_xu_ly': query_han_xu_ly,
        'query_loai_xu_ly': query_loai_xu_ly,
        'coming_soon_count': len(coming_soon_list),
        'overdue_count': len(overdue_list_all),
        'coming_soon_groups': coming_soon_groups,
        'overdue_groups': overdue_groups,
        'report_count': report_count,
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
            # Chấp nhận cả JSON (cũ) và FormData (mới có đính kèm file)
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                so_ky_hieu = data.get('so_ky_hieu')
                user_id = data.get('user_id')
                han_xu_ly = data.get('han_xu_ly')
                ghi_chu = data.get('ghi_chu')
                doc_type = data.get('doc_type', 'den')
                tep_moi = None
            else:
                so_ky_hieu = request.POST.get('so_ky_hieu')
                user_id = request.POST.getlist('user_id')
                han_xu_ly = request.POST.get('han_xu_ly')
                ghi_chu = request.POST.get('ghi_chu')
                doc_type = request.POST.get('doc_type', 'den')
                tep_moi = request.FILES.get('tep_dinh_kem')

            if not (is_tgd(request.user) or is_tp_it(request.user) or is_truong_phong(request.user)):
                return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền phân công!'}, status=403)

            if not han_xu_ly:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập thời hạn xử lý!'}, status=400)

            from datetime import datetime
            han_xu_ly_date = datetime.strptime(han_xu_ly, '%Y-%m-%d').date()
            if han_xu_ly_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Thời hạn xử lý không được nhỏ hơn ngày hiện tại!'},
                                    status=400)

            user_ids = user_id if isinstance(user_id, list) else [user_id]

            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDi'
                id_doituong = vb.VanBanDiID
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDen'
                id_doituong = vb.VanBanDenID

            # Nếu có tệp mới, cập nhật cho văn bản gốc
            if tep_moi:
                vb.TepDinhKem = tep_moi
                vb.save()

            from web.models import ThongBao
            for uid in user_ids:
                user = get_object_or_404(UserAccount, pk=uid)

                # Tạo hoặc cập nhật phân công
                if doc_type == 'di':
                    phan_cong, created = PhanCong.objects.get_or_create(
                        VanBanDiID=vb,
                        UserID=user,
                        defaults={'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu,
                                  'TrangThaiXuLy': 'Đang xử lý'}
                    )
                else:
                    phan_cong, created = PhanCong.objects.get_or_create(
                        VanBanDenID=vb,
                        UserID=user,
                        defaults={'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu,
                                  'TrangThaiXuLy': 'Đang xử lý'}
                    )
                if not created:
                    phan_cong.HanXuLy = han_xu_ly
                    phan_cong.GhiChu = ghi_chu
                    phan_cong.save()

                # Gửi thông báo đến người được phân công (hiển thị trên icon thông báo Logo bar)
                try:
                    han_str = han_xu_ly_date.strftime('%d/%m/%Y')
                    assigner_name = request.user.HoTen or request.user.username
                    trich_yeu = vb.TrichYeu or 'Không có trích yếu'
                    note_str = f" Ghi chú: {ghi_chu}." if ghi_chu else ""
                    ThongBao.objects.create(
                        UserID=user,
                        PhanCongID=phan_cong,
                        VanBanDenID=vb if doc_type != 'di' else None,
                        VanBanDiID=vb if doc_type == 'di' else None,
                        TieuDe=f"📋 [Phân công mới] Văn bản {so_ky_hieu}",
                        NoiDung=f"Đ/c {assigner_name} đã phân công bạn xử lý văn bản '{so_ky_hieu}'. Trích yếu: {trich_yeu}. Hạn xử lý: {han_str}.{note_str}",
                        LoaiThongBao=ThongBao.LoaiThongBaoChoices.PHAN_CONG,
                        LienKet=f"/xu-ly-van-ban/?so_ky_hieu={so_ky_hieu}"
                    )
                except Exception as notif_err:
                    print(f"Lỗi tạo thông báo phân công: {notif_err}")

            # Cập nhật trạng thái văn bản gốc
            if doc_type == 'di':
                # Giữ nguyên trạng thái hiện tại theo yêu cầu
                pass
            else:
                vb.TrangThai = VanBanDen.TrangThaiChoices.DANG_XU_LY
                vb.save()

            # Ghi lịch sử hoạt động
            msg_history = f"Phân công cho {len(user_ids)} người xử lý. Hạn: {han_xu_ly}"
            if tep_moi:
                msg_history += f" (Đã đính kèm tệp: {tep_moi.name})"

            LichSuHoatDong.objects.create(
                UserID=request.user,
                LoaiDoiTuong=loai_doi_tuong,
                DoiTuongID=id_doituong,
                HanhDong='Phân công',
                NoiDungThayDoi=msg_history
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

            if new_status == 'Hoàn thành':
                if doc_type == 'den':
                    vb.TrangThai = VanBanDen.TrangThaiChoices.HOAN_THANH
                else:
                    vb.TrangThai = VanBanDi.TrangThaiChoices.DA_PHAT_HANH
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
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                so_ky_hieu = data.get('so_ky_hieu')
                user_id = data.get('user_id')
                noi_dung = data.get('noi_dung')
                doc_type = data.get('doc_type', 'den')
                tep_moi = None
            else:
                so_ky_hieu = request.POST.get('so_ky_hieu')
                user_id = request.POST.getlist('user_id')
                noi_dung = request.POST.get('noi_dung')
                doc_type = request.POST.get('doc_type', 'den')
                tep_moi = request.FILES.get('tep_dinh_kem')

            user_ids = user_id if isinstance(user_id, list) else [user_id]

            if doc_type == 'di':
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDi'
                id_doituong = vb.VanBanDiID
            else:
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                loai_doi_tuong = 'VanBanDen'
                id_doituong = vb.VanBanDenID

            # Cập nhật tệp mới nếu có
            if tep_moi:
                vb.TepDinhKem = tep_moi
                vb.save()

            from web.models import ThongBao
            for uid in user_ids:
                user = get_object_or_404(UserAccount, pk=uid)
                if doc_type == 'di':
                    ChuyenTiep.objects.create(VanBanDiID=vb, UserID=user, NgayChuyenTiep=timezone.now())
                else:
                    ChuyenTiep.objects.create(VanBanDenID=vb, UserID=user, NgayChuyenTiep=timezone.now())

                # Gửi thông báo chuyển tiếp văn bản
                try:
                    assigner_name = request.user.HoTen or request.user.username
                    trich_yeu = vb.TrichYeu or 'Không có trích yếu'
                    note_str = f" Nội dung: {noi_dung}." if noi_dung else ""
                    ThongBao.objects.create(
                        UserID=user,
                        VanBanDenID=vb if doc_type != 'di' else None,
                        VanBanDiID=vb if doc_type == 'di' else None,
                        TieuDe=f"📨 [Chuyển tiếp] Văn bản {so_ky_hieu}",
                        NoiDung=f"Đ/c {assigner_name} đã chuyển tiếp văn bản '{so_ky_hieu}' cho bạn. Trích yếu: {trich_yeu}.{note_str}",
                        LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                        LienKet=f"/xu-ly-van-ban/?so_ky_hieu={so_ky_hieu}"
                    )
                except Exception as notif_err:
                    print(f"Lỗi tạo thông báo chuyển tiếp: {notif_err}")

            # Ghi lịch sử
            msg_history = f"Chuyển tiếp văn bản cho {len(user_ids)} người. Nội dung: {noi_dung}"
            if tep_moi:
                msg_history += f" (Đã đính kèm tệp: {tep_moi.name})"

            LichSuHoatDong.objects.create(
                UserID=request.user,
                LoaiDoiTuong=loai_doi_tuong,
                DoiTuongID=id_doituong,
                HanhDong='Chuyển tiếp',
                NoiDungThayDoi=msg_history
            )

            return JsonResponse({'status': 'success', 'message': 'Chuyển tiếp thành công!'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


@login_required
@csrf_exempt
def api_bao_cao_xlvb(request):
    """
    Nơi đưa ra các quyết định, hành động cho các văn bản cần ý kiến
    và tiếp nhận báo cáo xử lý văn bản không phù hợp:
    - Nếu xử lý văn bản có yêu cầu xin ý kiến:
        * Đồng ý / Phê duyệt đề xuất (DONG_Y)
        * Ý kiến chỉ đạo thực hiện (CHI_DAO)
        * Yêu cầu chỉnh sửa / Bổ sung (YEU_CAU_CHINH_SUA)
        * Chuyển tiếp xin ý kiến cấp trên (Giám đốc) (CHUYEN_TIEP_CAP_TREN)
        * Báo cáo không phù hợp / Trả lại (KHONG_PHU_HOP)
        * Cập nhật trạng thái BaoCao sang DA_GIAI_QUYET, gửi thông báo chuông cho người xin ý kiến
    - Nếu báo cáo vấn đề mới: tạo bản ghi BaoCao tương ứng.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            so_ky_hieu = data.get('so_ky_hieu')
            action = data.get('action') or data.get('huong_xu_ly') or data.get('loai_van_de')
            mo_ta = data.get('mo_ta') or data.get('noi_dung_chi_dao') or ''
            doc_type = data.get('doc_type', 'den')
            recipient_id = data.get('recipient_id')
            report_id = data.get('report_id')
            tep_moi = None
        else:
            so_ky_hieu = request.POST.get('so_ky_hieu')
            action = request.POST.get('action') or request.POST.get('huong_xu_ly') or request.POST.get('loai_van_de')
            mo_ta = request.POST.get('mo_ta') or request.POST.get('noi_dung_chi_dao') or ''
            doc_type = request.POST.get('doc_type', 'den')
            recipient_id = request.POST.get('recipient_id')
            report_id = request.POST.get('report_id')
            tep_moi = request.FILES.get('tep_dinh_kem')

        if doc_type == 'di':
            vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
            loai_doi_tuong = 'VanBanDi'
            id_doituong = vb.VanBanDiID
        else:
            vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
            loai_doi_tuong = 'VanBanDen'
            id_doituong = vb.VanBanDenID

        now = timezone.now()

        # Kiểm tra xem có BaoCao xin ý kiến đang chờ giải quyết cho văn bản này không
        report = None
        if report_id:
            report = BaoCao.objects.filter(pk=report_id).first()
        if not report:
            if request.user.is_giam_doc():
                report = BaoCao.objects.filter(
                    Q(VanBanDenID=vb) if doc_type == 'den' else Q(VanBanDiID=vb),
                    LoaiBaoCao='XIN_Y_KIEN',
                    TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
                ).order_by('-NgayBaoCao').first()
            else:
                report = BaoCao.objects.filter(
                    Q(VanBanDenID=vb) if doc_type == 'den' else Q(VanBanDiID=vb),
                    RecipientID=request.user,
                    LoaiBaoCao='XIN_Y_KIEN',
                    TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
                ).order_by('-NgayBaoCao').first()

        action_names = {
            'DONG_Y': 'Phê duyệt / Đồng ý đề xuất',
            'CHI_DAO': 'Ý kiến chỉ đạo thực hiện',
            'YEU_CAU_CHINH_SUA': 'Yêu cầu chỉnh sửa / Bổ sung',
            'CHUYEN_TIEP_CAP_TREN': 'Chuyển tiếp xin ý kiến cấp trên (Giám đốc)',
            'KHONG_PHU_HOP': 'Báo cáo không phù hợp / Trả lại',
            'v1': 'Sai sót nội dung',
            'v2': 'Chậm trễ xử lý',
            'v3': 'Lỗi file đính kèm',
            'v4': 'Vấn đề khác'
        }
        action_label = action_names.get(action, action or 'Xử lý văn bản')

        if report:
            # Đang đưa ra quyết định / chỉ đạo cho văn bản xin ý kiến
            report.HuongXuLy = action
            report.NoiDungXuLy = mo_ta
            report.ResolvedAt = now
            report.TrangThai = 'DA_GIAI_QUYET'
            report.save()

            # Cập nhật trạng thái văn bản theo quyết định
            if action in ['DONG_Y', 'CHI_DAO']:
                vb.TrangThai = 'DANG_XU_LY'
            elif action == 'YEU_CAU_CHINH_SUA':
                vb.TrangThai = 'CAN_XU_LY_LAI'
            elif action == 'CHUYEN_TIEP_CAP_TREN':
                vb.TrangThai = 'CAN_XU_LY_LAI'
                # Trưởng phòng chuyển tiếp lên Giám đốc
                gds = UserAccount.objects.filter(
                    Q(VaiTroID__ChucVu__icontains='Giám đốc') | Q(is_superuser=True)
                ).exclude(VaiTroID__ChucVu__icontains='Trưởng phòng').exclude(username='admin_temp').distinct()
                target_gd = gds.first()
                if target_gd:
                    BaoCao.objects.create(
                        VanBanDenID=vb if doc_type == 'den' else None,
                        VanBanDiID=vb if doc_type == 'di' else None,
                        UserID=request.user,
                        RecipientID=target_gd,
                        NgayBaoCao=now,
                        LoaiBaoCao='XIN_Y_KIEN',
                        GhiChu=f"Trưởng phòng {request.user.HoTen} chuyển tiếp lên Giám đốc: {mo_ta[:180]}",
                        TrangThai='CHUA_XEM',
                        TrangThaiVBCu=vb.TrangThai
                    )
                    ChuyenTiep.objects.create(
                        VanBanDenID=vb if doc_type == 'den' else None,
                        VanBanDiID=vb if doc_type == 'di' else None,
                        UserID=target_gd,
                        NgayChuyenTiep=now,
                        MucDoUuTien='Khẩn cấp'
                    )
                    ThongBao.objects.create(
                        UserID=target_gd,
                        VanBanDenID=vb if doc_type == 'den' else None,
                        VanBanDiID=vb if doc_type == 'di' else None,
                        TieuDe=f"📨 [Chuyển tiếp ý kiến] Văn bản {vb.SoKyHieu}",
                        NoiDung=f"Trưởng phòng {request.user.HoTen} ({request.user.role_name}) chuyển tiếp văn bản '{vb.SoKyHieu}' xin ý kiến Giám đốc. Ý kiến: {mo_ta}",
                        LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                        LienKet=f"/xu-ly-van-ban/?so_ky_hieu={vb.SoKyHieu}"
                    )
            elif action == 'KHONG_PHU_HOP':
                vb.TrangThai = 'CAN_XU_LY_LAI'
            vb.save()

            # Thông báo chuông cho người gửi yêu cầu xin ý kiến ban đầu
            if report.UserID and report.UserID != request.user:
                ThongBao.objects.create(
                    UserID=report.UserID,
                    VanBanDenID=vb if doc_type == 'den' else None,
                    VanBanDiID=vb if doc_type == 'di' else None,
                    TieuDe=f"📢 [Ý kiến chỉ đạo] Văn bản {vb.SoKyHieu}",
                    NoiDung=f"Lãnh đạo {request.user.HoTen} ({request.user.role_name}) đã ra quyết định: {action_label}. Ý kiến chỉ đạo: {mo_ta}",
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                    LienKet=f"/xu-ly-van-ban/?so_ky_hieu={vb.SoKyHieu}"
                )

            success_msg = f"Đã ban hành quyết định ({action_label}) cho văn bản '{vb.SoKyHieu}' thành công!"
        else:
            # Tạo báo cáo vấn đề mới thông thường
            trang_thai_cu = vb.TrangThai
            vb.TrangThai = 'CAN_XU_LY_LAI'
            vb.save()

            BaoCao.objects.create(
                VanBanDenID=vb if doc_type == 'den' else None,
                VanBanDiID=vb if doc_type == 'di' else None,
                UserID=request.user,
                RecipientID_id=recipient_id,
                NgayBaoCao=now,
                LoaiBaoCao=action,
                GhiChu=mo_ta[:250],
                TrangThai='CHUA_XEM',
                TrangThaiVBCu=trang_thai_cu
            )
            success_msg = f"Đã gửi báo cáo xử lý cho văn bản '{vb.SoKyHieu}' thành công!"

        # Cập nhật tệp mới nếu có
        if tep_moi:
            vb.TepDinhKem = tep_moi
            vb.save()

        # Ghi lịch sử hoạt động
        msg_history = f"Quyết định / Báo cáo xử lý: {action_label}. Nội dung: {mo_ta}"
        if tep_moi:
            msg_history += f" (Đã đính kèm tệp: {tep_moi.name})"

        LichSuHoatDong.objects.create(
            UserID=request.user,
            LoaiDoiTuong=loai_doi_tuong,
            DoiTuongID=id_doituong,
            HanhDong='Chỉ đạo / Quyết định',
            NoiDungThayDoi=msg_history
        )

        return JsonResponse({'status': 'success', 'message': success_msg})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def api_get_document_details(request):
    """API lấy thông tin chi tiết của văn bản based on ID and doc_type, kèm thông tin xin ý kiến nếu có"""
    doc_id = request.GET.get('id')
    doc_type = request.GET.get('doc_type', 'den')

    try:
        if doc_type == 'den':
            vb = get_object_or_404(VanBanDen, pk=doc_id)
        else:
            vb = get_object_or_404(VanBanDi, pk=doc_id)

        file_url = ''
        file_name = ''

        # Kiểm tra sự tồn tại của tệp đính kèm một cách an toàn
        if vb.TepDinhKem and hasattr(vb.TepDinhKem, 'url'):
            try:
                file_url = vb.TepDinhKem.url
                file_name = vb.TepDinhKem.name
            except ValueError:
                file_url = ''
                file_name = ''

        # Kiểm tra yêu cầu xin ý kiến đang chờ xử lý
        user = request.user
        filter_doc = Q(VanBanDenID=vb) if doc_type == 'den' else Q(VanBanDiID=vb)
        if user.is_giam_doc():
            r = BaoCao.objects.filter(
                filter_doc,
                TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
            ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan').order_by('-NgayBaoCao').first()
        elif user.is_department_head() or user.is_it_head():
            r = BaoCao.objects.filter(
                filter_doc,
                Q(RecipientID=user) | (Q(RecipientID__isnull=True) & Q(UserID__PhongBan=user.PhongBan)),
                TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
            ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan').order_by('-NgayBaoCao').first()
        else:
            r = BaoCao.objects.filter(
                filter_doc,
                RecipientID=user,
                TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
            ).exclude(LoaiBaoCao='Báo cáo tháng').select_related('UserID', 'UserID__PhongBan').order_by('-NgayBaoCao').first()

        xyk_info = None
        if r:
            xyk_info = {
                'report_id': r.PhanHoiID,
                'nguoi_gui': r.UserID.HoTen or r.UserID.username,
                'role_nguoi_gui': r.UserID.role_name or 'Cán bộ',
                'phong_ban': r.UserID.PhongBan.TenDonVi if r.UserID.PhongBan else '',
                'ly_do': r.GhiChu or '',
                'ngay_gui': r.NgayBaoCao.strftime('%d/%m/%Y %H:%M') if r.NgayBaoCao else '',
                'loai_bao_cao': r.LoaiBaoCao,
                'trang_thai': r.TrangThai
            }

        # Người nhận mặc định: Người xin ý kiến chỉ đạo (hoặc người gửi/soạn văn bản)
        default_recipient_id = None
        default_recipient_name = None
        if r and r.UserID:
            default_recipient_id = r.UserID.UserID
            default_recipient_name = r.UserID.HoTen or r.UserID.username
        elif vb.UserID:
            default_recipient_id = vb.UserID.UserID
            default_recipient_name = vb.UserID.HoTen or vb.UserID.username
        elif hasattr(vb, 'NguoiGui') and vb.NguoiGui:
            default_recipient_id = vb.NguoiGui.UserID
            default_recipient_name = vb.NguoiGui.HoTen or vb.NguoiGui.username

        if xyk_info:
            xyk_info['sender_id'] = default_recipient_id

        data = {
            'SoKyHieu': vb.SoKyHieu,
            'TrichYeu': vb.TrichYeu,
            'TepDinhKemUrl': file_url,
            'TepDinhKemName': file_name,
            'xin_y_kien': xyk_info,
            'is_xin_y_kien': bool(xyk_info),
            'default_recipient_id': default_recipient_id,
            'default_recipient_name': default_recipient_name,
            'is_truong_phong': user.is_department_head() or user.is_it_head(),
            'is_giam_doc': user.is_giam_doc()
        }
        return JsonResponse({'status': 'success', 'data': data, 'message': 'Lấy dữ liệu thành công'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def api_lay_danh_sach_bao_cao(request):
    """Lấy danh sách các báo cáo gửi cho mình (hoặc tất cả nếu là TGĐ)"""
    user = request.user
    if is_tgd(user):
        reports = BaoCao.objects.filter(TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']).exclude(LoaiBaoCao='Báo cáo tháng')
    elif user.is_department_head() or user.is_it_head():
        reports = BaoCao.objects.filter(
            Q(RecipientID=user) | (Q(RecipientID__isnull=True) & Q(UserID__PhongBan=user.PhongBan)),
            TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']
        ).exclude(LoaiBaoCao='Báo cáo tháng')
    else:
        reports = BaoCao.objects.filter(RecipientID=user, TrangThai__in=['CHUA_XEM', 'DANG_XU_LY']).exclude(LoaiBaoCao='Báo cáo tháng')
    
    reports = reports.select_related('UserID', 'VanBanDiID', 'VanBanDenID').order_by('-NgayBaoCao')
    
    data = []
    problem_map = {
        'v1': 'Sai sót nội dung',
        'v2': 'Chậm trễ xử lý',
        'v3': 'Lỗi file đính kèm',
        'v4': 'Vấn đề khác',
        'XIN_Y_KIEN': 'Xin ý kiến chỉ đạo'
    }
    for r in reports:
        vb = r.VanBanDiID if r.VanBanDiID else r.VanBanDenID
        loai_label = 'Xin ý kiến chỉ đạo' if r.LoaiBaoCao == 'XIN_Y_KIEN' else problem_map.get(r.LoaiBaoCao, r.LoaiBaoCao)
        
        file_url = ''
        file_name = ''
        if vb and vb.TepDinhKem and hasattr(vb.TepDinhKem, 'url'):
            try:
                file_url = vb.TepDinhKem.url
                file_name = vb.TepDinhKem.name.split('/')[-1]
            except Exception:
                pass

        data.append({
            'id': r.PhanHoiID,
            'so_ky_hieu': vb.SoKyHieu if vb else 'N/A',
            'trich_yeu': vb.TrichYeu if vb else 'N/A',
            'nguoi_bao_cao': r.UserID.HoTen or r.UserID.username,
            'role_nguoi_bao_cao': r.UserID.role_name or 'Cán bộ',
            'phong_ban_nguoi_bao_cao': r.UserID.PhongBan.TenDonVi if r.UserID.PhongBan else '',
            'sender_id': r.UserID.UserID,
            'loai_bao_cao': loai_label,
            'is_xin_y_kien': r.LoaiBaoCao == 'XIN_Y_KIEN',
            'ghi_chu': r.GhiChu or '',
            'ngay_bao_cao': r.NgayBaoCao.strftime('%d/%m/%Y %H:%M') if r.NgayBaoCao else '',
            'trang_thai': r.TrangThai,
            'doc_type': 'di' if r.VanBanDiID else 'den',
            'vb_id': vb.pk if vb else None,
            'file_url': file_url,
            'file_name': file_name
        })
    
    return JsonResponse({'status': 'success', 'data': data})

@login_required
@csrf_exempt
def api_xu_ly_bao_cao_action(request):
    """Xử lý báo cáo: Sửa / Chuyển / Từ chối"""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)
    
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        action = data.get('action') # 'SUA', 'CHUYEN', 'TU_CHOI'
        noi_dung = data.get('noi_dung')
        new_recipient_id = data.get('new_recipient_id')
        
        report = get_object_or_404(BaoCao, pk=report_id)
        vb = report.VanBanDiID if report.VanBanDiID else report.VanBanDenID
        loai_doi_tuong = 'VanBanDi' if report.VanBanDiID else 'VanBanDen'
        
        # Kiểm tra quyền
        if not (request.user == report.RecipientID or is_tgd(request.user)):
             return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền xử lý báo cáo này!'}, status=403)
        
        report.HuongXuLy = action
        report.NoiDungXuLy = noi_dung
        report.ResolvedAt = timezone.now()
        
        if action == 'SUA':
            # Khi chọn sửa, văn bản quay lại trạng thái hoạt động bình thường (Đang xử lý)
            vb.TrangThai = 'DANG_XU_LY'
            vb.save()
            report.TrangThai = 'DA_GIAI_QUYET'
            msg = "Đã chấp nhận báo cáo và chuyển trạng thái văn bản về Đang xử lý."
        
        elif action == 'CHUYEN':
            # Chuyển cho người khác xử lý báo cáo này
            if not new_recipient_id:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn người nhận mới!'}, status=400)
            report.RecipientID_id = new_recipient_id
            report.TrangThai = 'CHUA_XEM' # Reset trạng thái cho người mới
            msg = f"Đã chuyển báo cáo cho người khác xử lý."
            # Không kết thúc báo cáo ở đây, chỉ đổi người nhận
            report.save()
            return JsonResponse({'status': 'success', 'message': msg})
            
        elif action == 'TU_CHOI':
            # Từ chối báo cáo, khôi phục lại trạng thái cũ của văn bản
            if report.TrangThaiVBCu:
                vb.TrangThai = report.TrangThaiVBCu
            else:
                vb.TrangThai = 'DANG_XU_LY'
            vb.save()
            report.TrangThai = 'DA_GIAI_QUYET'
            msg = "Đã từ chối báo cáo, văn bản quay lại trạng thái cũ."
            
        report.save()
        
        # Ghi lịch sử
        LichSuHoatDong.objects.create(
            UserID=request.user,
            LoaiDoiTuong=loai_doi_tuong,
            DoiTuongID=vb.pk,
            HanhDong='Xử lý báo cáo',
            NoiDungThayDoi=f"Kết quả: {report.get_HuongXuLy_display()}. Nội dung: {noi_dung}"
        )
        
        return JsonResponse({'status': 'success', 'message': 'Xử lý báo cáo thành công!'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)



# ==============================================================================
# MODULE: QUẢN LÝ TIẾN ĐỘ & XỬ LÝ CHẬM TIẾN ĐỘ (THEO SƠ ĐỒ BPMN)
# ==============================================================================

@login_required
def quan_ly_tien_do_index(request):
    """
    Màn hình Quản lý & Theo dõi Tiến độ:
    - Mặc định chỉ hiển thị các văn bản CẦN XỬ LÝ GẤP (Sắp quá hạn <= 2 ngày và Quá hạn)
    - Cung cấp các thao tác: Cảnh báo đôn đốc, Xử lý quá hạn (Gia hạn, Chuyển người, Giải trình),
      và Lập báo cáo tổng hợp tiến độ để trình Giám đốc bên ngoài.
    """
    user = request.user
    today = timezone.now().date()
    now = timezone.now()

    # 1. Cập nhật quá hạn tự động (có cache tránh chậm DB)
    from django.core.cache import cache
    cache_key = f'update_overdue_tasks_{today}'
    if not cache.get(cache_key):
        PhanCong.objects.filter(
            HanXuLy__date__lt=today
        ).exclude(TrangThaiXuLy='Hoàn thành').exclude(TrangThaiXuLy='Quá hạn').update(TrangThaiXuLy='Quá hạn')
        cache.set(cache_key, True, timeout=900)

    # 2. Xác định phạm vi xem theo quyền
    base_qs = PhanCong.objects.select_related(
        'UserID', 'UserID__PhongBan',
        'VanBanDenID', 'VanBanDenID__DonViTrongID', 'VanBanDenID__DonViNgoaiID',
        'VanBanDiID', 'VanBanDiID__DonViTrongID', 'VanBanDiID__DonViNgoaiID'
    ).order_by('HanXuLy')

    if is_tgd(user) or is_tp_it(user):
        tasks = base_qs.all()
    elif is_truong_phong(user):
        tasks = base_qs.filter(
            Q(UserID__PhongBan=user.PhongBan) |
            Q(VanBanDenID__DonViTrongID=user.PhongBan) |
            Q(VanBanDiID__DonViTrongID=user.PhongBan)
        ).distinct()
    else:
        tasks = base_qs.filter(UserID=user)

    # 3. Bộ lọc tìm kiếm
    keyword = request.GET.get('keyword', '').strip()
    filter_phong_ban = request.GET.get('phong_ban', '').strip()
    filter_nguoi_xu_ly = request.GET.get('nguoi_xu_ly', '').strip()
    current_tab = request.GET.get('tab', 'can_xu_ly')

    if keyword:
        tasks = tasks.filter(
            Q(VanBanDenID__SoKyHieu__icontains=keyword) |
            Q(VanBanDenID__TrichYeu__icontains=keyword) |
            Q(VanBanDiID__SoKyHieu__icontains=keyword) |
            Q(VanBanDiID__TrichYeu__icontains=keyword) |
            Q(UserID__HoTen__icontains=keyword)
        )

    if filter_phong_ban and str(filter_phong_ban).isdigit() and (is_tgd(user) or is_tp_it(user)):
        tasks = tasks.filter(
            Q(UserID__PhongBan_id=filter_phong_ban) |
            Q(VanBanDenID__DonViTrongID_id=filter_phong_ban) |
            Q(VanBanDiID__DonViTrongID_id=filter_phong_ban)
        )

    if filter_nguoi_xu_ly:
        tasks = tasks.filter(UserID__HoTen__icontains=filter_nguoi_xu_ly)

    # 4. Phân loại tiến độ từng nhiệm vụ
    task_list = list(tasks)
    
    count_total = len(task_list)
    count_completed = 0
    count_coming_soon = 0
    count_overdue = 0
    count_extended = 0
    count_normal = 0

    coming_soon_list = []
    overdue_list = []
    extended_list = []
    completed_list = []
    normal_list = []

    for pc in task_list:
        vb = pc.VanBanDenID if pc.VanBanDenID else pc.VanBanDiID
        pc.vb_obj = vb
        pc.doc_type = 'den' if pc.VanBanDenID else 'di'
        pc.so_ky_hieu = vb.SoKyHieu if vb else '---'
        pc.trich_yeu = vb.TrichYeu if vb else '---'
        pc.loai_vb = vb.LoaiVanBan if (vb and hasattr(vb, 'LoaiVanBan')) else '---'
        
        han_date = pc.HanXuLy.date() if pc.HanXuLy else None

        if pc.TrangThaiXuLy == 'Hoàn thành':
            pc.status_key = 'hoan_thanh'
            pc.status_text = 'Đã hoàn thành'
            pc.badge_class = 'status-completed'
            count_completed += 1
            completed_list.append(pc)
        elif pc.PhuongAnXuLyCham == 'GIA_HAN' or (pc.SoLanGiaHan and pc.SoLanGiaHan > 0):
            pc.status_key = 'da_gia_han'
            pc.status_text = f'Đã gia hạn (Lần {pc.SoLanGiaHan})'
            pc.badge_class = 'status-extended'
            count_extended += 1
            extended_list.append(pc)
        elif pc.PhuongAnXuLyCham == 'GIAI_TRINH':
            pc.status_key = 'da_giai_trinh'
            pc.status_text = 'Đã giải trình'
            pc.badge_class = 'status-resolved'
            count_extended += 1
            extended_list.append(pc)
        elif han_date and han_date < today:
            days_over = (today - han_date).days
            pc.status_key = 'qua_han'
            pc.status_text = f'Quá hạn {days_over} ngày'
            pc.badge_class = 'status-overdue'
            count_overdue += 1
            overdue_list.append(pc)
        elif han_date and han_date <= today + timedelta(days=2):
            days_left = (han_date - today).days
            days_text = 'Hôm nay' if days_left == 0 else f'Còn {days_left} ngày'
            pc.status_key = 'sap_qua_han'
            pc.status_text = f'Sắp quá hạn ({days_text})'
            pc.badge_class = 'status-warning'
            count_coming_soon += 1
            coming_soon_list.append(pc)
        else:
            pc.status_key = 'dung_han'
            pc.status_text = 'Đang xử lý (Đúng hạn)'
            pc.badge_class = 'status-processing'
            count_normal += 1
            normal_list.append(pc)

    count_urgent = count_coming_soon + count_overdue

    # 5. Lọc theo tab hiển thị (MẶC ĐỊNH CHỈ HIỆN VĂN BẢN NGUY CƠ: SẮP QUÁ HẠN & QUÁ HẠN)
    if current_tab == 'sap_qua_han':
        display_items = coming_soon_list
    elif current_tab == 'qua_han':
        display_items = overdue_list
    elif current_tab == 'da_gia_han':
        display_items = extended_list
    elif current_tab == 'hoan_thanh':
        display_items = completed_list
    elif current_tab == 'tat_ca':
        display_items = task_list
    else:  # 'can_xu_ly' - Mặc định
        display_items = overdue_list + coming_soon_list

    # 6. Phân trang
    page_number = request.GET.get('page', 1)
    paginator = Paginator(display_items, 10)
    page_obj = paginator.get_page(page_number)

    # 7. Danh sách phòng ban và người dùng để lọc / điều chuyển
    don_vi_list = DonViBenTrong.objects.all().order_by('SoThuTu')
    if is_truong_phong(user) and user.PhongBan:
        user_assign_list = UserAccount.objects.filter(PhongBan=user.PhongBan, trang_thai='ACTIVE').only('UserID', 'HoTen')
    else:
        user_assign_list = UserAccount.objects.filter(trang_thai='ACTIVE').only('UserID', 'HoTen')

    context = {
        'page_obj': page_obj,
        'current_tab': current_tab,
        'count_total': count_total,
        'count_urgent': count_urgent,
        'count_coming_soon': count_coming_soon,
        'count_overdue': count_overdue,
        'count_extended': count_extended,
        'count_normal': count_normal,
        'count_completed': count_completed,
        'keyword': keyword,
        'filter_phong_ban': filter_phong_ban,
        'filter_nguoi_xu_ly': filter_nguoi_xu_ly,
        'don_vi_list': don_vi_list,
        'user_assign_list': user_assign_list,
        'today': today,
        'is_manager': is_tgd(user) or is_tp_it(user) or is_truong_phong(user),
    }
    return render(request, 'quan_ly_tien_do/index.html', context)


@login_required
@csrf_exempt
def api_canh_bao_tien_do(request):
    """
    API gửi cảnh báo đôn đốc tiến độ:
    - Áp dụng cho từng văn bản hoặc gửi hàng loạt cho các văn bản sắp quá hạn.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ!'}, status=405)

    user = request.user
    if not (is_tgd(user) or is_tp_it(user) or is_truong_phong(user)):
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền gửi cảnh báo đôn đốc!'}, status=403)

    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            pc_ids = data.get('phan_cong_ids', [])
            loi_nhan = data.get('loi_nhan', '').strip()
        else:
            pc_ids = request.POST.getlist('phan_cong_ids')
            single_id = request.POST.get('phan_cong_id')
            if single_id and not pc_ids:
                pc_ids = [single_id]
            loi_nhan = request.POST.get('loi_nhan', '').strip()

        if not pc_ids:
            # Nếu gửi hàng loạt không truyền ID, tự động lấy các task sắp quá hạn trong phạm vi quản lý
            today = timezone.now().date()
            base_qs = PhanCong.objects.filter(
                HanXuLy__date__range=[today, today + timedelta(days=2)]
            ).exclude(TrangThaiXuLy='Hoàn thành')
            if is_truong_phong(user) and user.PhongBan:
                base_qs = base_qs.filter(
                    Q(UserID__PhongBan=user.PhongBan) | Q(VanBanDenID__DonViTrongID=user.PhongBan)
                )
            pc_ids = list(base_qs.values_list('PhanCongID', flat=True))

        if not pc_ids:
            return JsonResponse({'status': 'error', 'message': 'Không tìm thấy văn bản nào cần gửi cảnh báo!'}, status=400)

        now = timezone.now()
        updated_count = 0

        for pc in PhanCong.objects.filter(PhanCongID__in=pc_ids).select_related('UserID', 'VanBanDenID', 'VanBanDiID'):
            pc.NgayCanhBaoCuoi = now
            pc.save(update_fields=['NgayCanhBaoCuoi'])

            vb = pc.VanBanDenID if pc.VanBanDenID else pc.VanBanDiID
            skh = vb.SoKyHieu if vb else '---'
            msg = loi_nhan or f'Đôn đốc tiến độ xử lý văn bản: {skh}. Yêu cầu hoàn thành đúng hạn!'

            LichSuHoatDong.objects.create(
                UserID=user,
                LoaiDoiTuong='PhanCong',
                DoiTuongID=pc.PhanCongID,
                HanhDong='Cảnh báo tiến độ',
                NoiDungThayDoi=f'Đã gửi cảnh báo đôn đốc tới {pc.UserID.HoTen}: {msg}'
            )
            # Gửi thông báo đôn đốc vào hộp thông báo người phụ trách
            if pc.UserID:
                try:
                    from web.models import ThongBao
                    ThongBao.objects.create(
                        UserID=pc.UserID,
                        PhanCongID=pc,
                        VanBanDenID=pc.VanBanDenID,
                        VanBanDiID=pc.VanBanDiID,
                        TieuDe=f"🔔 [Đôn đốc tiến độ] Văn bản {skh}",
                        NoiDung=f"Đ/c {user.HoTen or user.username} gửi nhắc nhở đôn đốc tiến độ xử lý văn bản '{skh}'. Yêu cầu khẩn trương hoàn thành đúng hạn!",
                        LoaiThongBao=ThongBao.LoaiThongBaoChoices.NHAC_NHO,
                        LienKet=f"/xu-ly-van-ban/?so_ky_hieu={skh}"
                    )
                except Exception as notif_err:
                    print(f"Lỗi tạo thông báo đôn đốc: {notif_err}")

            updated_count += 1

        return JsonResponse({
            'status': 'success',
            'message': f'Đã gửi cảnh báo đôn đốc thành công cho {updated_count} văn bản!'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
@csrf_exempt
def api_xu_ly_qua_han(request):
    """
    Quy trình riêng xử lý văn bản quá hạn:
    - Phương án 1 (GIA_HAN): Gia hạn thêm thời gian + lý do giải trình.
    - Phương án 2 (CHUYEN_NGUOI): Điều chuyển người xử lý khác.
    - Phương án 3 (GIAI_TRINH): Ghi nhận giải trình lý do trễ hạn.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Phương thức không hợp lệ!'}, status=405)

    user = request.user
    if not (is_tgd(user) or is_tp_it(user) or is_truong_phong(user)):
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền thực hiện xử lý chậm tiến độ!'}, status=403)

    try:
        import json
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            pc_id = data.get('phan_cong_id')
            phuong_an = data.get('phuong_an') # GIA_HAN, CHUYEN_NGUOI, GIAI_TRINH
            han_moi = data.get('han_moi')
            ly_do = data.get('ly_do', '').strip()
            user_moi_id = data.get('user_moi_id')
        else:
            pc_id = request.POST.get('phan_cong_id')
            phuong_an = request.POST.get('phuong_an')
            han_moi = request.POST.get('han_moi')
            ly_do = request.POST.get('ly_do', '').strip()
            user_moi_id = request.POST.get('user_moi_id')

        pc = get_object_or_404(PhanCong, pk=pc_id)
        vb = pc.VanBanDenID if pc.VanBanDenID else pc.VanBanDiID
        skh = vb.SoKyHieu if vb else '---'

        if phuong_an == 'GIA_HAN':
            if not han_moi:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn hạn xử lý mới!'}, status=400)
            if not ly_do:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập lý do gia hạn!'}, status=400)

            from datetime import datetime, time
            han_moi_date = datetime.strptime(han_moi, '%Y-%m-%d').date()
            if han_moi_date <= timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Hạn xử lý mới phải lớn hơn ngày hiện tại!'}, status=400)

            pc.HanXuLyCu = pc.HanXuLy
            pc.HanXuLy = timezone.make_aware(datetime.combine(han_moi_date, time(23, 59, 59)))
            pc.SoLanGiaHan = (pc.SoLanGiaHan or 0) + 1
            pc.LyDoChamTienDo = ly_do
            pc.PhuongAnXuLyCham = 'GIA_HAN'
            pc.TrangThaiXuLy = 'Đang xử lý'
            pc.save()

            LichSuHoatDong.objects.create(
                UserID=user,
                LoaiDoiTuong='PhanCong',
                DoiTuongID=pc.PhanCongID,
                HanhDong='Gia hạn tiến độ',
                NoiDungThayDoi=f'Gia hạn văn bản {skh} đến ngày {han_moi}. Lý do: {ly_do} (Gia hạn lần {pc.SoLanGiaHan})'
            )
            if pc.UserID:
                try:
                    from web.models import ThongBao
                    assigner_name = user.HoTen or user.username
                    ThongBao.objects.create(
                        UserID=pc.UserID,
                        PhanCongID=pc,
                        VanBanDenID=pc.VanBanDenID,
                        VanBanDiID=pc.VanBanDiID,
                        TieuDe=f"🕒 [Gia hạn tiến độ] Văn bản {skh}",
                        NoiDung=f"Đ/c {assigner_name} đã gia hạn thời gian xử lý văn bản '{skh}' đến ngày {han_moi}. Lý do: {ly_do}",
                        LoaiThongBao=ThongBao.LoaiThongBaoChoices.HE_THONG,
                        LienKet=f"/xu-ly-van-ban/?so_ky_hieu={skh}"
                    )
                except Exception as notif_err:
                    print(f"Lỗi tạo thông báo gia hạn: {notif_err}")

            return JsonResponse({'status': 'success', 'message': f'Gia hạn thành công đến ngày {han_moi}!'})

        elif phuong_an == 'CHUYEN_NGUOI':
            if not user_moi_id:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn người xử lý thay thế!'}, status=400)
            user_moi = get_object_or_404(UserAccount, pk=user_moi_id)
            user_cu_name = pc.UserID.HoTen if pc.UserID else 'Chưa có'

            pc.UserID = user_moi
            pc.PhuongAnXuLyCham = 'CHUYEN_NGUOI'
            pc.LyDoChamTienDo = ly_do or 'Điều chuyển nhân sự do chậm tiến độ'
            pc.save()

            LichSuHoatDong.objects.create(
                UserID=user,
                LoaiDoiTuong='PhanCong',
                DoiTuongID=pc.PhanCongID,
                HanhDong='Điều chuyển xử lý',
                NoiDungThayDoi=f'Điều chuyển văn bản {skh} từ {user_cu_name} sang {user_moi.HoTen}. Lý do: {pc.LyDoChamTienDo}'
            )

            # Gửi thông báo đến người được điều chuyển mới
            try:
                from web.models import ThongBao
                assigner_name = user.HoTen or user.username
                trich_yeu = vb.TrichYeu if vb else 'Không có trích yếu'
                han_str = pc.HanXuLy.strftime('%d/%m/%Y') if pc.HanXuLy else 'Chưa xác định'
                ThongBao.objects.create(
                    UserID=user_moi,
                    PhanCongID=pc,
                    VanBanDenID=pc.VanBanDenID,
                    VanBanDiID=pc.VanBanDiID,
                    TieuDe=f"📋 [Tiếp nhận xử lý] Văn bản {skh}",
                    NoiDung=f"Đ/c {assigner_name} đã điều chuyển bạn tiếp nhận xử lý văn bản '{skh}' thay cho {user_cu_name}. Trích yếu: {trich_yeu}. Hạn xử lý: {han_str}. Lý do: {pc.LyDoChamTienDo}",
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.PHAN_CONG,
                    LienKet=f"/xu-ly-van-ban/?so_ky_hieu={skh}"
                )
            except Exception as notif_err:
                print(f"Lỗi gửi thông báo điều chuyển: {notif_err}")

            return JsonResponse({'status': 'success', 'message': f'Đã điều chuyển văn bản sang cho {user_moi.HoTen}!'})

        elif phuong_an == 'GIAI_TRINH':
            if not ly_do:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập nội dung giải trình lý do trễ hạn!'}, status=400)

            pc.PhuongAnXuLyCham = 'GIAI_TRINH'
            pc.LyDoChamTienDo = ly_do
            pc.save()

            LichSuHoatDong.objects.create(
                UserID=user,
                LoaiDoiTuong='PhanCong',
                DoiTuongID=pc.PhanCongID,
                HanhDong='Giải trình chậm tiến độ',
                NoiDungThayDoi=f'Ghi nhận giải trình chậm tiến độ văn bản {skh}: {ly_do}'
            )
            return JsonResponse({'status': 'success', 'message': 'Đã ghi nhận nội dung giải trình thành công!'})

        else:
            return JsonResponse({'status': 'error', 'message': 'Phương án xử lý không hợp lệ!'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@login_required
def phieu_trinh_giam_doc(request):
    """
    Trang in phiếu trình Báo cáo tổng hợp tiến độ xử lý văn bản:
    - Định dạng chuẩn công văn, biểu mẫu hành chính trình Giám đốc bên ngoài.
    """
    user = request.user
    today = timezone.now().date()

    base_qs = PhanCong.objects.select_related(
        'UserID', 'UserID__PhongBan',
        'VanBanDenID', 'VanBanDenID__DonViTrongID', 'VanBanDenID__DonViNgoaiID',
        'VanBanDiID', 'VanBanDiID__DonViTrongID', 'VanBanDiID__DonViNgoaiID'
    ).order_by('HanXuLy')

    phong_ban_name = "Toàn công ty"
    if is_tgd(user) or is_tp_it(user):
        pb_id = request.GET.get('phong_ban')
        if pb_id and str(pb_id).isdigit():
            tasks = base_qs.filter(
                Q(UserID__PhongBan_id=pb_id) |
                Q(VanBanDenID__DonViTrongID_id=pb_id) |
                Q(VanBanDiID__DonViTrongID_id=pb_id)
            )
            pb = DonViBenTrong.objects.filter(pk=pb_id).first()
            if pb: phong_ban_name = pb.TenDonVi
        else:
            tasks = base_qs.all()
    elif is_truong_phong(user):
        tasks = base_qs.filter(
            Q(UserID__PhongBan=user.PhongBan) |
            Q(VanBanDenID__DonViTrongID=user.PhongBan) |
            Q(VanBanDiID__DonViTrongID=user.PhongBan)
        ).distinct()
        if user.PhongBan: phong_ban_name = user.PhongBan.TenDonVi
    else:
        tasks = base_qs.filter(UserID=user)
        if user.PhongBan: phong_ban_name = user.PhongBan.TenDonVi

    task_list = list(tasks)
    for pc in task_list:
        vb = pc.VanBanDenID if pc.VanBanDenID else pc.VanBanDiID
        pc.vb_obj = vb
        pc.so_ky_hieu = vb.SoKyHieu if vb else '---'
        pc.trich_yeu = vb.TrichYeu if vb else '---'
        pc.loai_vb = vb.LoaiVanBan if (vb and hasattr(vb, 'LoaiVanBan')) else '---'
        han_date = pc.HanXuLy.date() if pc.HanXuLy else None

        if pc.TrangThaiXuLy == 'Hoàn thành':
            pc.tinh_trang = 'Hoàn thành đúng hạn'
        elif pc.PhuongAnXuLyCham == 'GIA_HAN':
            pc.tinh_trang = f'Đã gia hạn lần {pc.SoLanGiaHan}'
        elif pc.PhuongAnXuLyCham == 'GIAI_TRINH':
            pc.tinh_trang = 'Chậm tiến độ (Đã giải trình)'
        elif han_date and han_date < today:
            days = (today - han_date).days
            pc.tinh_trang = f'Chậm tiến độ ({days} ngày)'
        elif han_date and han_date <= today + timedelta(days=2):
            pc.tinh_trang = 'Sắp đến hạn'
        else:
            pc.tinh_trang = 'Đang xử lý (Đúng tiến độ)'

    context = {
        'tasks': task_list,
        'today': today,
        'user': user,
        'phong_ban_name': phong_ban_name,
        'total_count': len(task_list),
        'completed_count': sum(1 for t in task_list if t.TrangThaiXuLy == 'Hoàn thành'),
        'overdue_count': sum(1 for t in task_list if t.HanXuLy and t.HanXuLy.date() < today and t.TrangThaiXuLy != 'Hoàn thành'),
    }
    return render(request, 'quan_ly_tien_do/phieu_trinh.html', context)


@login_required
def api_chi_tiet_tien_do(request, pk):
    """
    API lấy chi tiết tiến độ, thông tin văn bản và toàn bộ lịch sử đôn đốc / gia hạn
    """
    pc = get_object_or_404(PhanCong.objects.select_related(
        'UserID', 'UserID__PhongBan',
        'VanBanDenID', 'VanBanDenID__DonViTrongID', 'VanBanDenID__DonViNgoaiID',
        'VanBanDiID', 'VanBanDiID__DonViTrongID', 'VanBanDiID__DonViNgoaiID'
    ), pk=pk)

    user = request.user
    if not (is_tgd(user) or is_tp_it(user)):
        if is_truong_phong(user):
            in_pb = (pc.UserID and pc.UserID.PhongBan == user.PhongBan) or                     (pc.VanBanDenID and pc.VanBanDenID.DonViTrongID == user.PhongBan) or                     (pc.VanBanDiID and pc.VanBanDiID.DonViTrongID == user.PhongBan)
            if not in_pb:
                return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền xem văn bản này!'}, status=403)
        else:
            if pc.UserID != user:
                return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền xem văn bản này!'}, status=403)

    vb = pc.VanBanDenID if pc.VanBanDenID else pc.VanBanDiID
    doc_type = 'den' if pc.VanBanDenID else 'di'

    file_url = ''
    file_name = ''
    if vb and vb.TepDinhKem:
        try:
            file_url = vb.TepDinhKem.url
            file_name = str(vb.TepDinhKem.name).split('/')[-1]
        except Exception:
            pass

    lich_su = []
    logs = LichSuHoatDong.objects.filter(
        LoaiDoiTuong='PhanCong',
        DoiTuongID=pc.PhanCongID
    ).select_related('UserID').order_by('-ThoiGianCapNhat')

    for log in logs:
        lich_su.append({
            'time': log.ThoiGianCapNhat.strftime('%H:%M %d/%m/%Y'),
            'user': log.UserID.HoTen if log.UserID else 'Hệ thống',
            'action': log.HanhDong or 'Cập nhật',
            'content': log.NoiDungThayDoi or '',
        })

    don_vi = ''
    if pc.VanBanDenID:
        don_vi = pc.VanBanDenID.DonViGuiID.TenDonVi if pc.VanBanDenID.DonViGuiID else (pc.VanBanDenID.DonViNgoaiID.TenDonVi if pc.VanBanDenID.DonViNgoaiID else '')
    elif pc.VanBanDiID:
        don_vi = pc.VanBanDiID.DonViTrongID.TenDonVi if pc.VanBanDiID.DonViTrongID else (pc.VanBanDiID.DonViNgoaiID.TenDonVi if pc.VanBanDiID.DonViNgoaiID else '')

    ngay_vb = ''
    if pc.VanBanDenID:
        ngay_vb = pc.VanBanDenID.NgayNhan.strftime('%d/%m/%Y') if pc.VanBanDenID.NgayNhan else ''
    elif pc.VanBanDiID:
        ngay_vb = pc.VanBanDiID.NgayBanHanh.strftime('%d/%m/%Y') if pc.VanBanDiID.NgayBanHanh else ''

    data = {
        'phan_cong_id': pc.PhanCongID,
        'doc_type': 'Văn bản đến' if doc_type == 'den' else 'Văn bản đi',
        'so_ky_hieu': vb.SoKyHieu if vb else '---',
        'trich_yeu': vb.TrichYeu if vb else '---',
        'loai_vb': vb.LoaiVanBan if (vb and hasattr(vb, 'LoaiVanBan')) else '---',
        'don_vi': don_vi or 'Chưa xác định',
        'ngay_vb': ngay_vb or '---',
        'nguoi_xu_ly': pc.UserID.HoTen if pc.UserID else 'Chưa phân công',
        'phong_ban': pc.UserID.PhongBan.TenDonVi if (pc.UserID and pc.UserID.PhongBan) else 'Ban Giám đốc',
        
        'ngay_phan_cong': pc.NgayPhanCong.strftime('%d/%m/%Y') if pc.NgayPhanCong else '---',
        'han_xu_ly': pc.HanXuLy.strftime('%d/%m/%Y') if pc.HanXuLy else '---',
        'han_xu_ly_cu': pc.HanXuLyCu.strftime('%d/%m/%Y') if pc.HanXuLyCu else '',
        'so_lan_gia_han': pc.SoLanGiaHan or 0,
        'trang_thai': pc.TrangThaiXuLy or 'Đang xử lý',
        'phuong_an_xu_ly': pc.PhuongAnXuLyCham or '',
        'ly_do_cham': pc.LyDoChamTienDo or '',
        'ngay_canh_bao_cuoi': pc.NgayCanhBaoCuoi.strftime('%H:%M %d/%m/%Y') if pc.NgayCanhBaoCuoi else '',
        'file_url': file_url,
        'file_name': file_name,
        'lich_su': lich_su,
    }
    return JsonResponse({'status': 'success', 'data': data})


# ==============================================================
# HỆ THỐNG THÔNG BÁO TỰ ĐỘNG (SẮP ĐẾN HẠN & QUÁ HẠN)
# ==============================================================

def kiem_tra_va_tao_thong_bao_tu_dong():
    """
    Tự động quét toàn bộ văn bản và sinh thông báo hệ thống:
    - Sắp đến hạn (còn <= 2 ngày)
    - Quá hạn
    Có cơ chế cache tránh query lặp lại nhiều lần trong khoảng thời gian ngắn.
    """
    from django.core.cache import cache
    from datetime import timedelta
    from django.utils import timezone
    from web.models import PhanCong, ThongBao, UserAccount
    from django.db.models import Q

    today = timezone.now().date()
    lock_key = f'auto_scan_notif_{today}_{timezone.now().hour}_{timezone.now().minute // 5}'
    if cache.get(lock_key):
        return
    cache.set(lock_key, True, timeout=300)

    # 1. Quét văn bản sắp đến hạn (0 <= ngày còn lại <= 2)
    coming_soon_tasks = PhanCong.objects.filter(
        HanXuLy__date__range=[today, today + timedelta(days=2)]
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related(
        'UserID', 'UserID__PhongBan', 'VanBanDenID', 'VanBanDiID'
    )

    giam_doc_list = list(UserAccount.objects.filter(
        Q(VaiTroID__ChucVu__icontains='Tổng giám đốc') |
        Q(VaiTroID__ChucVu__icontains='Giám đốc') |
        Q(is_superuser=True)
    ).distinct())

    for pc in coming_soon_tasks:
        vb = pc.VanBanDenID or pc.VanBanDiID
        skh = vb.SoKyHieu if vb else '---'
        han_date = pc.HanXuLy.date()
        days_left = (han_date - today).days

        if days_left == 0:
            time_str = "HÔM NAY là hạn chót"
        elif days_left == 1:
            time_str = "còn 1 ngày nữa đến hạn"
        else:
            time_str = f"còn {days_left} ngày nữa đến hạn"

        title = f"⏰ [Sắp đến hạn] Văn bản {skh}"
        content = f"Văn bản '{skh}' do đ/c {pc.UserID.HoTen} phụ trách {time_str} ({pc.HanXuLy.strftime('%d/%m/%Y')}). Vui lòng hoàn thành đúng hạn."
        link = f"/quan-ly-tien-do/?keyword={skh}"

        recipients = [pc.UserID]
        if pc.UserID.PhongBan:
            tp = UserAccount.objects.filter(
                PhongBan=pc.UserID.PhongBan,
                VaiTroID__ChucVu__icontains='Trưởng phòng'
            ).first()
            if tp and tp not in recipients:
                recipients.append(tp)

        for u in recipients:
            exists = ThongBao.objects.filter(
                UserID=u,
                PhanCongID=pc,
                LoaiThongBao=ThongBao.LoaiThongBaoChoices.SAP_QUA_HAN,
                NgayTao__date=today
            ).exists()
            if not exists:
                ThongBao.objects.create(
                    UserID=u,
                    PhanCongID=pc,
                    VanBanDenID=pc.VanBanDenID,
                    VanBanDiID=pc.VanBanDiID,
                    TieuDe=title,
                    NoiDung=content,
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.SAP_QUA_HAN,
                    LienKet=link
                )

    # 2. Quét văn bản quá hạn
    overdue_tasks = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related(
        'UserID', 'UserID__PhongBan', 'VanBanDenID', 'VanBanDiID'
    )
    overdue_tasks.exclude(TrangThaiXuLy='Quá hạn').update(TrangThaiXuLy='Quá hạn')

    for pc in overdue_tasks:
        vb = pc.VanBanDenID or pc.VanBanDiID
        skh = vb.SoKyHieu if vb else '---'
        days_overdue = (today - pc.HanXuLy.date()).days

        title = f"🚨 [Quá hạn {days_overdue} ngày] Văn bản {skh}"
        content = f"Văn bản '{skh}' do đ/c {pc.UserID.HoTen} phụ trách đã quá hạn {days_overdue} ngày (Hạn: {pc.HanXuLy.strftime('%d/%m/%Y')}). Cần xử lý gấp hoặc gia hạn/giải trình."
        link = f"/quan-ly-tien-do/?tab=qua_han&keyword={skh}"

        recipients = [pc.UserID]
        if pc.UserID.PhongBan:
            tp = UserAccount.objects.filter(
                PhongBan=pc.UserID.PhongBan,
                VaiTroID__ChucVu__icontains='Trưởng phòng'
            ).first()
            if tp and tp not in recipients:
                recipients.append(tp)

        for gd in giam_doc_list:
            if gd not in recipients:
                recipients.append(gd)

        for u in recipients:
            exists = ThongBao.objects.filter(
                UserID=u,
                PhanCongID=pc,
                LoaiThongBao=ThongBao.LoaiThongBaoChoices.QUA_HAN,
                NgayTao__date=today
            ).exists()
            if not exists:
                ThongBao.objects.create(
                    UserID=u,
                    PhanCongID=pc,
                    VanBanDenID=pc.VanBanDenID,
                    VanBanDiID=pc.VanBanDiID,
                    TieuDe=title,
                    NoiDung=content,
                    LoaiThongBao=ThongBao.LoaiThongBaoChoices.QUA_HAN,
                    LienKet=link
                )


def format_thoi_gian_truoc(dt):
    if not dt:
        return ''
    now = timezone.now()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return 'Vừa xong'
    elif seconds < 3600:
        return f'{seconds // 60} phút trước'
    elif seconds < 86400:
        return f'{seconds // 3600} giờ trước'
    elif seconds < 86400 * 2:
        return 'Hôm qua'
    else:
        return dt.strftime('%d/%m/%Y %H:%M')


@login_required
def api_thong_bao_danh_sach(request):
    """
    API lấy danh sách thông báo và số lượng chưa đọc của user hiện tại
    """
    try:
        kiem_tra_va_tao_thong_bao_tu_dong()
    except Exception as e:
        pass

    user = request.user
    from web.models import ThongBao
    unread_count = ThongBao.objects.filter(UserID=user, DaDoc=False).count()
    notifications_qs = ThongBao.objects.filter(UserID=user).order_by('-NgayTao')[:25]

    data = []
    for tb in notifications_qs:
        data.append({
            'id': tb.ThongBaoID,
            'title': tb.TieuDe,
            'content': tb.NoiDung,
            'type': tb.LoaiThongBao,
            'link': tb.LienKet or '/quan-ly-tien-do/',
            'is_read': tb.DaDoc,
            'time_ago': format_thoi_gian_truoc(tb.NgayTao),
            'created_at': tb.NgayTao.strftime('%H:%M %d/%m/%Y'),
        })

    return JsonResponse({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': data
    })


@login_required
@csrf_exempt
def api_thong_bao_danh_dau_da_doc(request):
    """
    API đánh dấu thông báo là đã đọc:
    - Nếu gửi all=1 hoặc tat_ca=1: Đánh dấu tất cả thông báo của user là đã đọc
    - Nếu gửi id: Đánh dấu 1 thông báo cụ thể là đã đọc
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    user = request.user
    from web.models import ThongBao

    try:
        import json
        if request.content_type == 'application/json':
            payload = json.loads(request.body)
            all_flag = payload.get('all') or payload.get('tat_ca')
            tb_id = payload.get('id')
        else:
            all_flag = request.POST.get('all') or request.POST.get('tat_ca')
            tb_id = request.POST.get('id')

        if all_flag in [True, 1, '1', 'true']:
            ThongBao.objects.filter(UserID=user, DaDoc=False).update(DaDoc=True)
            return JsonResponse({'status': 'success', 'message': 'Đã đánh dấu tất cả là đã đọc.'})

        if tb_id:
            ThongBao.objects.filter(UserID=user, pk=tb_id).update(DaDoc=True)
            return JsonResponse({'status': 'success', 'message': 'Đã đánh dấu thông báo là đã đọc.'})

        return JsonResponse({'status': 'error', 'message': 'Thiếu tham số!'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# ==============================================================================
# GIAI ĐOẠN 3 (PHASE 3): AI OCR, AI SMART SUMMARY & AI CLASSIFICATION
# ==============================================================================

@login_required
@csrf_exempt
def api_ocr_extract_document(request):
    """
    AUTO-01: OCR và Trích xuất thông tin tự động từ tệp văn bản (PDF, DOCX, Ảnh Scan)
    Tự động nhận dạng: Số ký hiệu, Loại văn bản, Ngày ban hành, Cơ quan ban hành, Trích yếu
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    uploaded_file = request.FILES.get('tep_dinh_kem') or request.FILES.get('file')
    if not uploaded_file:
        return JsonResponse({'status': 'error', 'message': 'Vui lòng tải lên tệp văn bản cần quét OCR!'}, status=400)

    from web.ai_services import extract_text_from_file, parse_ocr_administrative_metadata, classify_and_suggest_assignment

    try:
        raw_text = extract_text_from_file(uploaded_file, filename=uploaded_file.name)
        meta = parse_ocr_administrative_metadata(raw_text, filename=uploaded_file.name)
        classification = classify_and_suggest_assignment(raw_text, meta.get('trich_yeu', ''), meta.get('loai_van_ban', ''))

        from web.models import DonViBenNgoai
        dv_match = None
        if meta.get('co_quan_ban_hanh'):
            dv_match = DonViBenNgoai.objects.filter(TenDonVi__icontains=meta['co_quan_ban_hanh'][:15]).first()

        return JsonResponse({
            'status': 'success',
            'message': 'Đã nhận dạng và trích xuất thành công dữ liệu văn bản!',
            'data': {
                'so_ky_hieu': meta.get('so_ky_hieu', ''),
                'loai_van_ban': meta.get('loai_van_ban', 'Công văn'),
                'ngay_ban_hanh': meta.get('ngay_ban_hanh', ''),
                'co_quan_ban_hanh': meta.get('co_quan_ban_hanh', ''),
                'don_vi_ngoai_id': dv_match.DonViNgoaiID if dv_match else None,
                'trich_yeu': meta.get('trich_yeu', ''),
                'nguoi_ky': meta.get('nguoi_ky', ''),
                'raw_text_length': len(raw_text),
            },
            'classification': classification
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Lỗi phân tích OCR: {str(e)}'}, status=500)


@login_required
@csrf_exempt
def api_ai_summarize_document(request, pk):
    """
    AUTO-08: Nghiên cứu thông tin và Tóm tắt thông minh bằng AI (Executive Summary)
    Xuất ra bản tóm tắt ngắn gọn 3-5 ý chính, phân tích yêu cầu hành động, thời hạn
    """
    doc_type = request.GET.get('type') or request.POST.get('type') or 'den'
    refresh = request.GET.get('refresh') == '1' or request.POST.get('refresh') == '1'

    from web.models import VanBanDen, VanBanDi
    from web.ai_services import extract_text_from_file, generate_smart_summary

    if doc_type == 'di':
        doc = get_object_or_404(VanBanDi, pk=pk)
    else:
        doc = get_object_or_404(VanBanDen, pk=pk)

    if not refresh and getattr(doc, 'TomTatAI', None):
        return JsonResponse({
            'status': 'success',
            'cached': True,
            'summary_html': doc.TomTatAI,
            'linh_vuc': getattr(doc, 'LinhVucAI', 'Hành chính')
        })

    raw_text = ""
    if doc.TepDinhKem:
        try:
            if hasattr(doc.TepDinhKem, 'path') and os.path.exists(doc.TepDinhKem.path):
                raw_text = extract_text_from_file(doc.TepDinhKem.path, filename=doc.TepDinhKem.name)
            elif doc.TepDinhKem.storage.exists(doc.TepDinhKem.name):
                raw_text = extract_text_from_file(doc.TepDinhKem, filename=doc.TepDinhKem.name)
        except Exception as err:
            print(f"Lỗi đọc file tóm tắt AI: {err}")

    summary_result = generate_smart_summary(raw_text, trich_yeu=doc.TrichYeu, loai_vb=doc.LoaiVanBan)

    doc.TomTatAI = summary_result['html']
    doc.LinhVucAI = summary_result['summary_data']['linh_vuc']
    doc.save(update_fields=['TomTatAI', 'LinhVucAI'])

    return JsonResponse({
        'status': 'success',
        'cached': False,
        'summary_html': summary_result['html'],
        'summary_data': summary_result['summary_data'],
        'plain_text': summary_result['plain_text'],
        'linh_vuc': summary_result['summary_data']['linh_vuc']
    })


@login_required
def api_ai_suggest_assignment(request):
    """
    AUTO-07: Phân tích nội dung và Gợi ý phòng ban/nhân sự phân công cho Lãnh đạo
    """
    doc_id = request.GET.get('doc_id')
    doc_type = request.GET.get('doc_type', 'den')
    trich_yeu = request.GET.get('trich_yeu', '')
    loai_vb = request.GET.get('loai_vb', '')

    from web.models import VanBanDen, VanBanDi
    from web.ai_services import extract_text_from_file, classify_and_suggest_assignment

    raw_text = ""
    if doc_id:
        try:
            if doc_type == 'di':
                doc = VanBanDi.objects.get(pk=doc_id)
            else:
                doc = VanBanDen.objects.get(pk=doc_id)
            trich_yeu = doc.TrichYeu or trich_yeu
            loai_vb = doc.LoaiVanBan or loai_vb
            if doc.TepDinhKem:
                if hasattr(doc.TepDinhKem, 'path') and os.path.exists(doc.TepDinhKem.path):
                    raw_text = extract_text_from_file(doc.TepDinhKem.path, filename=doc.TepDinhKem.name)
                elif doc.TepDinhKem.storage.exists(doc.TepDinhKem.name):
                    raw_text = extract_text_from_file(doc.TepDinhKem, filename=doc.TepDinhKem.name)
        except Exception as e:
            print(f"Lỗi lấy văn bản để gợi ý AI: {e}")

    result = classify_and_suggest_assignment(raw_text, trich_yeu=trich_yeu, loai_vb=loai_vb)

    return JsonResponse({
        'status': 'success',
        'data': result
    })
