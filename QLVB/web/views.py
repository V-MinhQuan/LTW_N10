from django.shortcuts import render

# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from django.contrib.auth import login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Max
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
from .models import VanBanDen, DonViBenNgoai, LichSuHoatDong
from .forms import VanBanDenForm

# --- TRANG CHỦ & ĐĂNG NHẬP ---
def index(request):
    """View cho trang Dashboard"""
    return render(request, 'index.html')

def login(request):
    """View cho trang Đăng nhập"""
    return render(request, 'login.html')

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
            'NguoiThucHien': ls.UserID.HoTen if ls.UserID and ls.UserID.HoTen else (ls.UserID.username if ls.UserID else 'Hệ thống'),
            'HanhDong': ls.HanhDong,
            'NoiDungThayDoi': ls.NoiDungThayDoi
        })
    return JsonResponse({'status': 'success', 'data': data})

# --- QUẢN LÝ VĂN BẢN ĐI ---    
def van_ban_di_index(request):
    return render(request, 'van_ban_di/index.html')

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
    return render(request, 'quan_ly_don_vi/ben_ngoai.html')

def quan_ly_don_vi_ben_trong(request):
    return render(request, 'quan_ly_don_vi/ben_trong.html')

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
