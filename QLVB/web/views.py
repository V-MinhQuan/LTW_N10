from django.shortcuts import render

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

# --- QUẢN LÝ ĐƠN VỊ ---
def quan_ly_don_vi_ben_ngoai(request):
    return render(request, 'quan_ly_don_vi/ben_ngoai.html')

def quan_ly_don_vi_ben_trong(request):
    return render(request, 'quan_ly_don_vi/ben_trong.html')

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
