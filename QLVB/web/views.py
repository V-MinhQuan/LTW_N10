from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import DonViBenTrong, DonViBenNgoai, UserAccount, VanBanDen, PhanCong, ChuyenTiep, BaoCao, LichSuHoatDong
from django.utils import timezone
from datetime import timedelta
import json

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
    
    overdue_qs = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID')

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
        'overdue_count': overdue_qs.count(),
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
