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
            
        # Lưu lại giá trị cũ để so sánh
        old_data = {
            'Số ký hiệu': vbd.SoKyHieu,
            'Trích yếu': vbd.TrichYeu,
            'Loại văn bản': vbd.LoaiVanBan,
            'Ngày ban hành': vbd.NgayBanHanh.strftime('%d/%m/%Y') if vbd.NgayBanHanh else 'Trống',
            'Ngày nhận': vbd.NgayNhan.strftime('%d/%m/%Y') if vbd.NgayNhan else 'Trống',
            'Đơn vị gửi': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống',
            'Trạng thái': 'Đang xử lý' if vbd.TrangThai != 'HOAN_THANH' else 'Hoàn thành'
        }
        
        form = VanBanDenForm(request.POST, request.FILES)
        if form.is_valid():
            vbd = form.save(user=request.user if request.user.is_authenticated else None, instance=vbd)
            
            # So sánh dữ liệu mới
            new_data = {
                'Số ký hiệu': vbd.SoKyHieu,
                'Trích yếu': vbd.TrichYeu,
                'Loại văn bản': vbd.LoaiVanBan,
                'Ngày ban hành': vbd.NgayBanHanh.strftime('%d/%m/%Y') if vbd.NgayBanHanh else 'Trống',
                'Ngày nhận': vbd.NgayNhan.strftime('%d/%m/%Y') if vbd.NgayNhan else 'Trống',
                'Đơn vị gửi': vbd.DonViNgoaiID.TenDonVi if vbd.DonViNgoaiID else 'Trống',
                'Trạng thái': 'Đang xử lý' if vbd.TrangThai != 'HOAN_THANH' else 'Hoàn thành'
            }
            
            changes = []
            for field, old_val in old_data.items():
                new_val = new_data.get(field)
                if old_val != new_val:
                    changes.append(f"{field}: {old_val} -> {new_val}")
            
            if changes:
                try:
                    LichSuHoatDong.objects.create(
                        UserID=request.user if request.user.is_authenticated else None,
                        LoaiDoiTuong='VanBanDen',
                        DoiTuongID=vbd.VanBanDenID,
                        HanhDong='Cập nhật',
                        NoiDungThayDoi='Thay đổi: ' + ', '.join(changes)
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
