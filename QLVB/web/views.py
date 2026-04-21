from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from .models import DonViBenTrong, DonViBenNgoai, UserAccount, VanBanDen, VanBanDi, PhanCong, ChuyenTiep, BaoCao, LichSuHoatDong
from django.utils import timezone
from datetime import timedelta
import json
from itertools import chain

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
    # Tự động hoàn thành các văn bản đã quá thời hạn xử lý
    today = timezone.now().date()
    overdue_to_update = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành')
    
    if overdue_to_update.exists():
        overdue_to_update.update(TrangThaiXuLy='Quá hạn')
        # Chúng ta không tự động cập nhật trạng thái văn bản gốc sang Hoàn thành/Đã phát hành 
        # để người dùng có thể thấy trạng thái Quá hạn (màu đỏ) trong danh sách.

    query_so_ky_hieu = request.GET.get('so_ky_hieu', '')
    query_nguoi_xu_ly = request.GET.get('nguoi_xu_ly', '')
    query_ngay_nhan = request.GET.get('ngay_nhan', '')
    page_number = request.GET.get('page', 1)
    
    # Lấy danh sách Văn bản đến
    docs_den = VanBanDen.objects.select_related('DonViNgoaiID', 'UserID').all()
    if query_so_ky_hieu:
        docs_den = docs_den.filter(SoKyHieu__icontains=query_so_ky_hieu)
    if query_nguoi_xu_ly and query_nguoi_xu_ly != '--- Chọn người xử lý ---':
        docs_den = docs_den.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly)
    if query_ngay_nhan:
        try:
            day, month, year = query_ngay_nhan.split('/')
            docs_den = docs_den.filter(NgayNhan__date=f"{year}-{month}-{day}")
        except: pass
    for d in docs_den: 
        d.doc_type = 'den'
        d.sort_date = d.NgayNhan

    # Lấy danh sách Văn bản đi
    docs_di = VanBanDi.objects.select_related('DonViNgoaiID', 'DonViTrongID', 'UserID').all()
    if query_so_ky_hieu:
        docs_di = docs_di.filter(SoKyHieu__icontains=query_so_ky_hieu)
    if query_nguoi_xu_ly and query_nguoi_xu_ly != '--- Chọn người xử lý ---':
        docs_di = docs_di.filter(phancong__UserID__HoTen__icontains=query_nguoi_xu_ly)
    if query_ngay_nhan:
        try:
            day, month, year = query_ngay_nhan.split('/')
            docs_di = docs_di.filter(NgayBanHanh__date=f"{year}-{month}-{day}")
        except: pass
    for d in docs_di: 
        d.doc_type = 'di'
        d.sort_date = d.NgayBanHanh

    # Gộp và sắp xếp
    documents = sorted(
        chain(docs_den, docs_di),
        key=lambda x: x.sort_date if x.sort_date else timezone.now(),
        reverse=True
    )

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
    
    overdue_qs = PhanCong.objects.filter(
        HanXuLy__date__lt=today
    ).exclude(TrangThaiXuLy='Hoàn thành').select_related('VanBanDenID', 'VanBanDiID')

    # Nhóm theo số ngày
    coming_soon_groups = {}
    for pc in coming_soon_qs:
        doc = pc.VanBanDenID or pc.VanBanDiID
        if doc:
            days = (pc.HanXuLy.date() - today).days
            days_str = "Hôm nay" if days == 0 else f"còn {days} ngày"
            if days_str not in coming_soon_groups:
                coming_soon_groups[days_str] = []
            coming_soon_groups[days_str].append(doc.SoKyHieu)

    overdue_groups = {}
    for pc in overdue_qs:
        doc = pc.VanBanDenID or pc.VanBanDiID
        if doc:
            days = (today - pc.HanXuLy.date()).days
            days_str = f"quá hạn {days} ngày"
            if days_str not in overdue_groups:
                overdue_groups[days_str] = []
            overdue_groups[days_str].append(doc.SoKyHieu)

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
            doc_type = data.get('doc_type', 'den') # Mặc định là 'den'
            
            if doc_type == 'den':
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = vb, None
            else:
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = None, vb
            
            # Xử lý trường hợp user_id rỗng
            if not user_id:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng chọn ít nhất một người xử lý!'}, status=400)
                
            if not han_xu_ly:
                return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập thời hạn xử lý!'}, status=400)
                
            from datetime import datetime
            han_xu_ly_date = datetime.strptime(han_xu_ly, '%Y-%m-%d').date()
            if han_xu_ly_date < timezone.now().date():
                return JsonResponse({'status': 'error', 'message': 'Thời hạn xử lý không được nhỏ hơn ngày hiện tại!'}, status=400)
                
            # user_id có thể là list hoặc 1 string
            user_ids = user_id if isinstance(user_id, list) else [user_id]
            
            for uid in user_ids:
                user = get_object_or_404(UserAccount, pk=uid)
                
                # Cập nhật hoặc tạo mới phân công cho từng người nhận
                phan_cong, created = PhanCong.objects.get_or_create(
                    VanBanDenID=vb_den,
                    VanBanDiID=vb_di,
                    UserID=user,
                    defaults={'NgayPhanCong': timezone.now(), 'HanXuLy': han_xu_ly, 'GhiChu': ghi_chu, 'TrangThaiXuLy': 'Đang xử lý'}
                )
                
                if not created:
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
            doc_type = data.get('doc_type', 'den')
            
            if doc_type == 'den':
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                phan_cong = PhanCong.objects.filter(VanBanDenID=vb).first()
            else:
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                phan_cong = PhanCong.objects.filter(VanBanDiID=vb).first()
            
            if not phan_cong:
                return JsonResponse({'status': 'error', 'message': 'Văn bản chưa được phân công!'}, status=400)
            
            old_status = phan_cong.TrangThaiXuLy
            new_status = 'Đang xử lý' if trang_thai_id == '1' else 'Hoàn thành'
            
            phan_cong.TrangThaiXuLy = new_status
            phan_cong.save()
            
            if new_status == 'Hoàn thành':
                vb.TrangThai = VanBanDen.TrangThaiChoices.HOAN_THANH if doc_type == 'den' else VanBanDi.TrangThaiChoices.DA_PHAT_HANH # Hoặc trạng thái phù hợp cho VanBanDi
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
            don_vi_id = data.get('don_vi_id') 
            noi_dung = data.get('noi_dung')
            doc_type = data.get('doc_type', 'den')
            
            if doc_type == 'den':
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = vb, None
            else:
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = None, vb
            
            # Ghi nhận chuyển tiếp
            ChuyenTiep.objects.create(
                VanBanDenID=vb_den,
                VanBanDiID=vb_di,
                UserID=request.user if request.user.is_authenticated else UserAccount.objects.first(),
                NgayChuyenTiep=timezone.now(),
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
            doc_type = data.get('doc_type', 'den')
            
            if doc_type == 'den':
                vb = get_object_or_404(VanBanDen, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = vb, None
            else:
                vb = get_object_or_404(VanBanDi, SoKyHieu=so_ky_hieu)
                vb_den, vb_di = None, vb
            
            BaoCao.objects.create(
                VanBanDenID=vb_den,
                VanBanDiID=vb_di,
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

def api_get_document_details(request):
    """API lấy thông tin chi tiết của văn bản based on ID and doc_type"""
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
                # Trường hợp có tên tệp trong DB nhưng tệp thực tế không tồn tại/không có URL
                file_url = ''
                file_name = ''
            
        data = {
            'SoKyHieu': vb.SoKyHieu,
            'TrichYeu': vb.TrichYeu,
            'TepDinhKemUrl': file_url,
            'TepDinhKemName': file_name
        }
        return JsonResponse({'status': 'success', 'data': data, 'message': 'Lấy dữ liệu thành công'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

