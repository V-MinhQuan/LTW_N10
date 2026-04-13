from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q, Max
from django.core.paginator import Paginator
from .models import DonViBenTrong, DonViBenNgoai, UserAccount, VaiTro
import json

from django.shortcuts import render, redirect
# IMPORT ĐẦY ĐỦ CHO HỆ THỐNG ĐĂNG NHẬP
from django.contrib.auth import authenticate, login as auth_login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
# IMPORT CHO HỆ THỐNG THÔNG BÁO LỖI (MESSAGES)
from django.contrib import messages
from .forms import LoginForm


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

#--THÔNG TIN NGƯỜI DÙNG--
@login_required(login_url='/login/')
def thong_tin_view(request):
    # Xử lý đổi mật khẩu từ Popup
    if request.method == 'POST' and 'old_password' in request.POST:
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not request.user.check_password(old_password):
            messages.error(request, 'Mật khẩu hiện tại không đúng!')
            request.session['open_modal'] = True
        elif new_password != confirm_password:
            messages.error(request, 'Mật khẩu mới không khớp!')
            request.session['open_modal'] = True
        else:
            # Đổi pass thành công
            request.user.set_password(new_password)
            request.user.save()
            # Cực kỳ quan trọng: Giữ lại phiên đăng nhập sau khi đổi pass
            update_session_auth_hash(request, request.user)
            messages.success(request, 'Đổi mật khẩu thành công!')
            request.session['open_modal'] = False

        return redirect('thong_tin') # Chú ý: url pattern của ông phải tên là 'thong_tin'

    # Load trang thông tin (GET)
    open_modal = request.session.pop('open_modal', False)

    return render(request, 'quan_ly_nguoi_dung/thong_tin.html', {
        'open_modal': open_modal
    })
# --- QUẢN LÝ VĂN BẢN ĐẾN ---
def van_ban_den_index(request):
    return render(request, 'van_ban_den/index.html')

# --- QUẢN LÝ VĂN BẢN ĐI ---    
def van_ban_di_index(request):
    return render(request, 'van_ban_di/index.html')

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
    return render(request, 'xu_ly_van_ban/index.html')

def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')

def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')

def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')

def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')

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
