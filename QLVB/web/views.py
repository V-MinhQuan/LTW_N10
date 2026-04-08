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
@login_required
def van_ban_den_index(request):
    return render(request, 'van_ban_den/index.html')


# --- QUẢN LÝ VĂN BẢN ĐI ---
@login_required
def van_ban_di_index(request):
    return render(request, 'van_ban_di/index.html')


# --- QUẢN LÝ NGƯỜI DÙNG ---
@login_required
def quan_ly_nguoi_dung_index(request):
    return render(request, 'quan_ly_nguoi_dung/index.html')


@login_required
def thong_tin_nguoi_dung(request):
    # Không cần lấy dữ liệu thủ công, Django đã lo hết qua biến 'request.user'
    return render(request, 'quan_ly_nguoi_dung/thong_tin.html')


# --- QUẢN LÝ ĐƠN VỊ ---
@login_required
def quan_ly_don_vi_ben_ngoai(request):
    return render(request, 'quan_ly_don_vi/ben_ngoai.html')


@login_required
def quan_ly_don_vi_ben_trong(request):
    return render(request, 'quan_ly_don_vi/ben_trong.html')


# --- XỬ LÝ VĂN BẢN ĐIỀU HÀNH ---
@login_required
def xu_ly_van_ban_index(request):
    return render(request, 'xu_ly_van_ban/index.html')


@login_required
def xu_ly_van_ban_bao_cao(request):
    return render(request, 'xu_ly_van_ban/bao_cao.html')


@login_required
def xu_ly_van_ban_cap_nhat(request):
    return render(request, 'xu_ly_van_ban/cap_nhat.html')


@login_required
def xu_ly_van_ban_chuyen_tiep(request):
    return render(request, 'xu_ly_van_ban/chuyen_tiep.html')


@login_required
def xu_ly_van_ban_phan_cong(request):
    return render(request, 'xu_ly_van_ban/phan_cong.html')