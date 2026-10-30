from django.db import models
from django.contrib.auth.models import AbstractUser

class VaiTro(models.Model):
    VaiTroID = models.AutoField(primary_key=True)
    ChucVu = models.CharField(max_length=50)
    PhongBan = models.ForeignKey('DonViBenTrong', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Thuộc phòng ban")

    def __str__(self):
        return f"{self.ChucVu} ({self.PhongBan.TenDonVi if self.PhongBan else 'Chưa gán'})"

    class Meta:
        verbose_name_plural = "Vai Trò"

class UserAccount(AbstractUser):
    UserID = models.AutoField(primary_key=True)
    VaiTroID = models.ForeignKey(VaiTro, on_delete=models.SET_NULL, null=True, blank=True)
    HoTen = models.CharField(max_length=100)
    SoDienThoai = models.CharField(max_length=15)
    NgaySinh = models.DateField(null=True, blank=True)
    GioiTinh = models.CharField(max_length=10, choices=[('Nam', 'Nam'), ('Nữ', 'Nữ')], null=True, blank=True)
    TrangThai = models.BooleanField(default=True)
    trang_thai = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    SoThuTu = models.IntegerField(default=0, null=True, blank=True)
    PhongBan = models.ForeignKey('DonViBenTrong', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Phòng ban")

    @property
    def role_name(self):
        return self.VaiTroID.ChucVu if self.VaiTroID else ""

    @property
    def is_admin_account(self):
        name = (self.HoTen or '').lower()
        uname = (self.username or '').lower()
        role = (self.role_name or '').lower()
        return 'admin' in uname or 'admin' in name or 'quản trị' in name or 'admin' in role or 'quản trị' in role

    @classmethod
    def get_operational_users(cls, phong_ban=None, is_active=True):
        """
        Lấy danh sách người dùng nghiệp vụ (tự động loại trừ các tài khoản quản trị hệ thống / admin).
        """
        from django.db.models import Q
        qs = cls.objects.all()
        if is_active:
            qs = qs.filter(Q(is_active=True) & (Q(trang_thai='ACTIVE') | Q(trang_thai__isnull=True)))

        # Loại trừ tài khoản Admin / Quản trị viên
        qs = qs.exclude(
            Q(username__icontains='admin') |
            Q(HoTen__icontains='Admin') |
            Q(HoTen__icontains='Quản trị') |
            Q(VaiTroID__ChucVu__icontains='Admin') |
            Q(VaiTroID__ChucVu__icontains='Quản trị')
        )
        if phong_ban:
            qs = qs.filter(PhongBan=phong_ban)
        return qs

    def is_giam_doc(self):
        if self.is_admin_account:
            return False
        return self.role_name == "Tổng giám đốc" or 'Giám đốc' in self.role_name or self.is_superuser

    def is_it_head(self):
        return self.role_name == "Trưởng phòng IT"

    def is_department_head(self):
        return self.role_name and self.role_name.startswith("Trưởng phòng") and not self.is_it_head()

    def is_nhan_vien(self):
        chuc_vu = self.role_name or ""
        return 'Nhân viên' in chuc_vu or 'Chuyên viên' in chuc_vu or 'CSKH' in chuc_vu or 'viên' in chuc_vu or 'Văn thư' in chuc_vu

    def can_approve(self):
        # Giám đốc có toàn quyền phê duyệt
        if self.is_giam_doc():
            return True
        # Trưởng phòng IT có quyền phê duyệt (có điều kiện, kiểm tra chi tiết ở can_perform_action)
        if self.is_it_head():
            return True
        # Các Trưởng phòng ban có quyền
        if self.is_department_head():
            return True
        # Admin hệ thống
        return self.is_superuser

    def can_publish(self):
        # Giám đốc có toàn quyền phát hành
        if self.is_giam_doc():
            return True
        # Trưởng phòng IT có quyền phát hành (có điều kiện, kiểm tra chi tiết ở can_perform_action)
        if self.is_it_head():
            return True
        # Các Trưởng phòng ban có quyền
        if self.is_department_head():
            return True
        # Admin hệ thống
        return self.is_superuser

    def can_manage_users_and_units(self):
        # Chỉ Giám đốc và TP IT mới có quyền quản lý người dùng, đơn vị
        if self.is_giam_doc() or self.is_it_head():
            return True
        # Trưởng phòng các phòng ban khác không có quyền này (kể cả khi là superuser)
        if self.is_department_head():
            return False
        # Admin hệ thống (superuser không thuộc vai trò Trưởng phòng ban khác)
        return self.is_superuser

    def can_perform_action(self, action, obj=None):
        # Giám đốc có toàn quyền hệ thống
        if self.is_giam_doc():
            return True

        # --- Trưởng phòng IT: xử lý riêng ---
        if self.is_it_head():
            if action in ['phe_duyet', 'phat_hanh']:
                # Không có đối tượng cụ thể: hiển thị nút chung (TP IT có quyền)
                if not obj:
                    return True
                if hasattr(obj, 'VanBanDiID') or hasattr(obj, 'SoKyHieu'):
                    # Quy tắc 1: Không được tự phê duyệt/phát hành văn bản do chính mình tạo
                    if hasattr(obj, 'NguoiGui') and obj.NguoiGui == self:
                        return False
                    # Quy tắc 2: Chỉ được phê duyệt/phát hành văn bản thuộc phòng IT
                    nguoi_gui_pb = obj.NguoiGui.PhongBan if (hasattr(obj, 'NguoiGui') and obj.NguoiGui) else None
                    user_id_pb = obj.UserID.PhongBan if (hasattr(obj, 'UserID') and obj.UserID) else None
                    if nguoi_gui_pb == self.PhongBan or user_id_pb == self.PhongBan:
                        return True
                return False
            # Các action khác: TP IT toàn quyền
            return True

        # --- Trưởng phòng các phòng ban nghiệp vụ: phê duyệt/ký nháy văn bản thuộc phòng ban mình ---
        if self.is_department_head():
            if action in ['phe_duyet', 'phat_hanh']:
                if not obj:
                    return True
                if hasattr(obj, 'VanBanDiID') or hasattr(obj, 'SoKyHieu'):
                    # Quy tắc 1: Không được tự phê duyệt văn bản do chính mình tạo (trừ khi tự giao việc)
                    if hasattr(obj, 'NguoiGui') and obj.NguoiGui == self and hasattr(obj, 'UserID') and obj.UserID != self:
                        return False
                    # Quy tắc 2: Phê duyệt/ký nháy văn bản thuộc phòng ban của mình
                    nguoi_gui_pb = obj.NguoiGui.PhongBan if (hasattr(obj, 'NguoiGui') and obj.NguoiGui) else None
                    user_id_pb = obj.UserID.PhongBan if (hasattr(obj, 'UserID') and obj.UserID) else None
                    don_vi_gui = getattr(obj, 'DonViGuiID', None)
                    if nguoi_gui_pb == self.PhongBan or user_id_pb == self.PhongBan or don_vi_gui == self.PhongBan:
                        return True
                return False
            # Các action khác tiếp tục xuống dưới
        elif self.is_superuser:
            return True

        # Kiểm tra cực kỳ nghiêm ngặt cho các vai trò khác: Chỉ người phụ trách (UserID) mới có quyền duyệt/phát hành văn bản đi cụ thể.
        if obj and hasattr(obj, 'VanBanDiID') and action in ['phe_duyet', 'phat_hanh']:
            if hasattr(obj, 'UserID') and obj.UserID != self:
                return False
        
        # Nếu thao tác với một đối tượng cụ thể (Văn bản)
        if obj and action in ['xem', 'sua', 'xoa']:
            is_vbd = getattr(obj, '_meta', None) and obj._meta.model_name == 'vanbanden'
            is_vbdi = getattr(obj, '_meta', None) and obj._meta.model_name == 'vanbandi'

            # Trưởng phòng (bao gồm cả IT): Chỉ được thao tác văn bản thuộc phòng mình soạn/xử lý
            if self.is_department_head() or self.is_it_head():
                # 1. Kiểm tra đơn vị nhận nội bộ (Chỉ áp dụng cho Văn bản đến)
                if is_vbd and hasattr(obj, 'DonViTrongID') and obj.DonViTrongID == self.PhongBan:
                    return True
                
                # 2. Kiểm tra người soạn/người xử lý chính (Cả đến và đi)
                if hasattr(obj, 'UserID') and obj.UserID and obj.UserID.PhongBan == self.PhongBan:
                    return True
                
                # 3. Kiểm tra người gửi (Chỉ áp dụng cho Văn bản đi)
                if is_vbdi and hasattr(obj, 'NguoiGui') and obj.NguoiGui and obj.NguoiGui.PhongBan == self.PhongBan:
                    return True
                # 4. Kiểm tra nhân viên trong phòng có được phân công/chuyển tiếp không
                from .models import PhanCong, ChuyenTiep
                if is_vbd:
                    if PhanCong.objects.filter(VanBanDenID=obj, UserID__PhongBan=self.PhongBan).exists(): return True
                    if ChuyenTiep.objects.filter(VanBanDenID=obj, UserID__PhongBan=self.PhongBan).exists(): return True
                elif is_vbdi:
                    if PhanCong.objects.filter(VanBanDiID=obj, UserID__PhongBan=self.PhongBan).exists(): return True
                    if ChuyenTiep.objects.filter(VanBanDiID=obj, UserID__PhongBan=self.PhongBan).exists(): return True
                
                return False

            # Nhân viên: Chỉ thao tác văn bản của mình tạo hoặc được phân công/chuyển tiếp
            if self.is_nhan_vien():
                # 1. Kiểm tra người tạo
                if hasattr(obj, 'UserID') and obj.UserID == self:
                    return True
                # 2. Kiểm tra phân công/chuyển tiếp
                from .models import PhanCong, ChuyenTiep
                is_assigned = False
                if is_vbd:
                    is_assigned = PhanCong.objects.filter(VanBanDenID=obj, UserID=self).exists() or \
                                  ChuyenTiep.objects.filter(VanBanDenID=obj, UserID=self).exists()
                elif is_vbdi:
                    is_assigned = PhanCong.objects.filter(VanBanDiID=obj, UserID=self).exists() or \
                                  ChuyenTiep.objects.filter(VanBanDiID=obj, UserID=self).exists()
                
                return is_assigned

        if action in ['phe_duyet', 'phat_hanh']:
            # 1. Phải có quyền phê duyệt/phát hành chung
            if not (self.can_approve() and self.can_publish()):
                return False
            
            # 2. Kiểm tra trên đối tượng Văn bản đi cụ thể
            if obj and hasattr(obj, 'VanBanDiID'):
                # Quy tắc: Không được tự phê duyệt văn bản mình tạo (NguoiGui) trừ khi mình chính là người được giao (UserID)
                if hasattr(obj, 'NguoiGui') and obj.NguoiGui == self:
                    if hasattr(obj, 'UserID') and obj.UserID == self:
                        return True
                    return False
                
                return True
            
            # Nếu không có đối tượng, trả về True nếu có quyền chung (để hiển thị menu/nút chung nếu cần)
            return not obj
            
        if action in ['quan_ly_nguoi_dung', 'quan_ly_don_vi']:
            return self.can_manage_users_and_units()
            
        if self.is_nhan_vien():
            return action in ['xem', 'sua', 'xoa', 'them']

        # Mặc định Trưởng phòng IT và các Trưởng phòng khác có các quyền còn lại (xem, sửa, xóa, thêm)
        return action in ['xem', 'sua', 'xoa', 'them']




    def __str__(self):
        return self.HoTen if self.HoTen else self.username

    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"

class DonViBenTrong(models.Model):
    DonViTrongID = models.AutoField(primary_key=True)
    TenDonVi = models.CharField(max_length=100)
    DiaChi = models.CharField(max_length=255, null=True, blank=True)
    SoDienThoai = models.CharField(max_length=15, null=True, blank=True)
    NguoiLienHe = models.CharField(max_length=100, null=True, blank=True)
    Email = models.EmailField(max_length=100, null=True, blank=True)
    SoThuTu = models.IntegerField(default=0, null=True, blank=True)
    trang_thai = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.TenDonVi

    class Meta:
        verbose_name_plural = "Đơn vị bên trong"

class DonViBenNgoai(models.Model):
    DonViNgoaiID = models.AutoField(primary_key=True)
    TenDonVi = models.CharField(max_length=100)
    DiaChi = models.CharField(max_length=255, null=True, blank=True)
    SoDienThoai = models.CharField(max_length=15, null=True, blank=True)
    NguoiLienHe = models.CharField(max_length=100, null=True, blank=True)
    Email = models.EmailField(max_length=100, null=True, blank=True)
    SoThuTu = models.IntegerField(default=0, null=True, blank=True)
    trang_thai = models.CharField(max_length=20, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def __str__(self):
        return self.TenDonVi

    class Meta:
        verbose_name_plural = "Đơn vị bên ngoài"

class VanBanDen(models.Model):
    class TrangThaiChoices(models.TextChoices):
        MOI = 'MOI', 'Mới'
        HOAN_THANH = 'HOAN_THANH', 'Hoàn thành'
        DANG_XU_LY = 'DANG_XU_LY', 'Đang xử lý'
        CAN_XU_LY_LAI = 'CAN_XU_LY_LAI', 'Cần xử lý lại'
        CHO_PHE_DUYET = 'CHO_PHE_DUYET', 'Chờ phê duyệt'
        DA_PHE_DUYET = 'DA_PHE_DUYET', 'Đã phê duyệt'
        DA_PHAT_HANH = 'DA_PHAT_HANH', 'Đã phát hành'

    VanBanDenID = models.AutoField(primary_key=True)
    DonViNgoaiID = models.ForeignKey(DonViBenNgoai, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    DonViGuiID = models.ForeignKey(DonViBenTrong, on_delete=models.SET_NULL, null=True, blank=True, related_name='vbd_den_gui_set', db_index=True)
    VanBanDiID = models.ForeignKey('VanBanDi', on_delete=models.SET_NULL, null=True, blank=True, related_name='vbd_link_set', db_index=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    SoKyHieu = models.CharField(max_length=50, db_index=True)
    NgayBanHanh = models.DateTimeField(null=True, blank=True, db_index=True)
    NgayNhan = models.DateTimeField(null=True, blank=True, db_index=True)
    LoaiVanBan = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    TrichYeu = models.CharField(max_length=255, null=True, blank=True)
    DonViTrongID = models.ForeignKey(DonViBenTrong, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DANG_XU_LY, db_index=True)
    NgayHoanThanh = models.DateTimeField(null=True, blank=True)
    TepDinhKem = models.FileField(upload_to='den/%Y/%m/', null=True, blank=True)
    TomTatAI = models.TextField(null=True, blank=True, verbose_name="Bản tóm tắt thông minh AI")
    LinhVucAI = models.CharField(max_length=100, null=True, blank=True, verbose_name="Lĩnh vực AI")
    GoiYPhanCongAI = models.JSONField(default=dict, blank=True, verbose_name="Gợi ý phân công AI")

    def __str__(self):
        return self.SoKyHieu

    class Meta:
        verbose_name_plural = "Văn bản đến"

class VanBanDi(models.Model):
    class TrangThaiChoices(models.TextChoices):
        DU_THAO = 'DU_THAO', 'Dự thảo'
        CHO_PHE_DUYET = 'CHO_PHE_DUYET', 'Chờ phê duyệt'
        DA_PHE_DUYET = 'DA_PHE_DUYET', 'Đã phê duyệt'
        DA_PHAT_HANH = 'DA_PHAT_HANH', 'Đã phát hành'
        CAN_SUA_DOI = 'CAN_SUA_DOI', 'Cần sửa đổi'
        CAN_XU_LY_LAI = 'CAN_XU_LY_LAI', 'Cần xử lý lại'

    VanBanDiID = models.AutoField(primary_key=True)
    DonViTrongID = models.ForeignKey(DonViBenTrong, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    DonViNgoaiID = models.ForeignKey(DonViBenNgoai, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    DonViGuiID = models.ForeignKey(DonViBenTrong, on_delete=models.SET_NULL, null=True, blank=True, related_name='vanbandi_gui_unit_set', db_index=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, db_index=True)
    NguoiGui = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='vanbandi_gui_set', db_index=True)
    SoKyHieu = models.CharField(max_length=50, db_index=True)
    NgayBanHanh = models.DateTimeField(null=True, blank=True, db_index=True)
    LoaiVanBan = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    TrichYeu = models.CharField(max_length=255, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DU_THAO, db_index=True)
    TepDinhKem = models.FileField(upload_to='di/%Y/%m/', null=True, blank=True)
    TomTatAI = models.TextField(null=True, blank=True, verbose_name="Bản tóm tắt thông minh AI")
    LinhVucAI = models.CharField(max_length=100, null=True, blank=True, verbose_name="Lĩnh vực AI")
    
    # Các trường bổ sung theo yêu cầu luồng mới
    NgayGuiPheDuyet = models.DateTimeField(null=True, blank=True)
    NgayPheDuyet = models.DateTimeField(null=True, blank=True)
    NgayPhatHanh = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.SoKyHieu

    class Meta:
        verbose_name_plural = "Văn bản đi"

class PhanCong(models.Model):
    class TrangThaiXuLyChoices(models.TextChoices):
        DANG_XU_LY = 'Đang xử lý', 'Đang xử lý'
        HOAN_THANH = 'Hoàn thành', 'Hoàn thành'
        QUA_HAN = 'Quá hạn', 'Quá hạn'

    PhanCongID = models.AutoField(primary_key=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_index=True)
    NgayPhanCong = models.DateTimeField(null=True, blank=True)
    HanXuLy = models.DateTimeField(null=True, blank=True, db_index=True)
    MucDoUuTien = models.CharField(max_length=50, null=True, blank=True)
    TrangThaiXuLy = models.CharField(max_length=50, choices=TrangThaiXuLyChoices.choices, null=True, blank=True, db_index=True)
    GhiChu = models.CharField(max_length=255, null=True, blank=True)
    
    # Các trường theo dõi tiến độ & xử lý chậm tiến độ theo quy trình BPMN
    HanXuLyCu = models.DateTimeField(null=True, blank=True, verbose_name="Hạn xử lý trước khi gia hạn")
    SoLanGiaHan = models.IntegerField(default=0, verbose_name="Số lần gia hạn")
    LyDoChamTienDo = models.TextField(null=True, blank=True, verbose_name="Lý do chậm tiến độ / gia hạn")
    PhuongAnXuLyCham = models.CharField(max_length=50, null=True, blank=True, verbose_name="Phương án xử lý chậm") # GIA_HAN, CHUYEN_NGUOI, GIAI_TRINH
    NgayCanhBaoCuoi = models.DateTimeField(null=True, blank=True, verbose_name="Thời điểm cảnh báo gần nhất")

    @property
    def van_ban(self):
        return self.VanBanDenID if self.VanBanDenID_id else self.VanBanDiID

    @property
    def trich_yeu(self):
        if hasattr(self, '_trich_yeu') and self._trich_yeu is not None:
            return self._trich_yeu
        vb = self.van_ban
        return vb.TrichYeu if vb else ""

    @trich_yeu.setter
    def trich_yeu(self, value):
        self._trich_yeu = value

    @property
    def so_ky_hieu(self):
        if hasattr(self, '_so_ky_hieu') and self._so_ky_hieu is not None:
            return self._so_ky_hieu
        vb = self.van_ban
        return vb.SoKyHieu if vb else ""

    @so_ky_hieu.setter
    def so_ky_hieu(self, value):
        self._so_ky_hieu = value

    class Meta:
        verbose_name_plural = "Phân công" 

class ChuyenTiep(models.Model):
    ChuyenTiepID = models.AutoField(primary_key=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_index=True)
    NgayChuyenTiep = models.DateTimeField(null=True, blank=True, db_index=True)
    NgayBatDau = models.DateTimeField(null=True, blank=True)
    NgayHetHan = models.DateTimeField(null=True, blank=True)
    MucDoUuTien = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Chuyển tiếp"

class LichSuHoatDong(models.Model):
    LichSuID = models.AutoField(primary_key=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE, db_index=True)
    LoaiDoiTuong = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    DoiTuongID = models.IntegerField(null=True, blank=True, db_index=True)
    HanhDong = models.CharField(max_length=50, null=True, blank=True)
    NoiDungThayDoi = models.TextField(null=True, blank=True)
    TrangThaiCu = models.CharField(max_length=50, null=True, blank=True)
    TrangThaiMoi = models.CharField(max_length=50, null=True, blank=True)
    ThoiGianCapNhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Lịch sử hoạt động"

class BaoCao(models.Model):
    class TrangThaiChoices(models.TextChoices):
        CHUA_XEM = 'CHUA_XEM', 'Chưa xem'
        DANG_XU_LY = 'DANG_XU_LY', 'Đang xử lý'
        DA_GIAI_QUYET = 'DA_GIAI_QUYET', 'Đã giải quyết'

    class HuongXuLyChoices(models.TextChoices):
        SUA = 'SUA', 'Sửa văn bản'
        CHUYEN = 'CHUYEN', 'Chuyển người xử lý'
        TU_CHOI = 'TU_CHOI', 'Từ chối báo cáo'

    PhanHoiID = models.AutoField(primary_key=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='baocao_gui_set')
    RecipientID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True, related_name='baocao_nhan_set')
    NgayBaoCao = models.DateTimeField(auto_now_add=True)
    LoaiBaoCao = models.CharField(max_length=50, null=True, blank=True)
    GhiChu = models.CharField(max_length=255, null=True, blank=True)
    
    # Các trường xử lý
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.CHUA_XEM)
    HuongXuLy = models.CharField(max_length=50, choices=HuongXuLyChoices.choices, null=True, blank=True)
    NoiDungXuLy = models.TextField(null=True, blank=True)
    TrangThaiVBCu = models.CharField(max_length=50, null=True, blank=True)
    ResolvedAt = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Báo cáo / Phản hồi"

class PheDuyet(models.Model):
    PheDuyetID = models.AutoField(primary_key=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NgayPheDuyet = models.DateTimeField(null=True, blank=True)
    TrangThaiDuyet = models.BooleanField(default=False)
    ChuKySo = models.TextField(null=True, blank=True)
    GhiChu = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Phê duyệt"

class PhatHanh(models.Model):
    PhatHanhID = models.AutoField(primary_key=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    TieuDe = models.CharField(max_length=255, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, null=True, blank=True)
    NgayPhatHanh = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Phát hành"

class Butphe(models.Model):
    ButPheID = models.AutoField(primary_key=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NoiDung = models.CharField(max_length=255, null=True, blank=True)
    NgayButPhe = models.DateTimeField(null=True, blank=True)
    MucDoKhan = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Bút phê"


class ThongBao(models.Model):
    class LoaiThongBaoChoices(models.TextChoices):
        SAP_QUA_HAN = 'SAP_QUA_HAN', 'Sắp quá hạn'
        QUA_HAN = 'QUA_HAN', 'Quá hạn'
        NHAC_NHO = 'NHAC_NHO', 'Nhắc nhở đôn đốc'
        PHAN_CONG = 'PHAN_CONG', 'Phân công xử lý'
        HE_THONG = 'HE_THONG', 'Hệ thống'

    ThongBaoID = models.AutoField(primary_key=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE, related_name='thong_bao_set', db_index=True)
    PhanCongID = models.ForeignKey(PhanCong, on_delete=models.CASCADE, null=True, blank=True, db_index=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    TieuDe = models.CharField(max_length=255)
    NoiDung = models.TextField()
    LoaiThongBao = models.CharField(max_length=30, choices=LoaiThongBaoChoices.choices, default=LoaiThongBaoChoices.HE_THONG)
    LienKet = models.CharField(max_length=255, null=True, blank=True)
    DaDoc = models.BooleanField(default=False, db_index=True)
    NgayTao = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        verbose_name_plural = "Thông báo hệ thống"
        ordering = ['-NgayTao']

    def __str__(self):
        return f"[{self.LoaiThongBao}] {self.TieuDe} -> {self.UserID.username}"


class NgoaiLeHeThong(models.Model):
    """
    AUTO-06: Xử lý sự cố kết nối và ngoại lệ hệ thống
    Tự động lưu trạng thái công việc bị gián đoạn (như lỗi mất mạng khi gửi mail,
    lỗi đồng bộ liên phòng ban, lỗi lưu tệp), hỗ trợ thử lại theo cơ chế cấu hình
    và thông báo cho quản trị viên.
    """
    class LoaiNgoaiLeChoices(models.TextChoices):
        GUI_EMAIL = 'GUI_EMAIL', 'Gửi email phát hành'
        DONG_BO_VAN_BAN = 'DONG_BO_VAN_BAN', 'Đồng bộ văn bản'
        LUU_TEP_TIN = 'LUU_TEP_TIN', 'Lưu trữ tệp tin'
        KET_NOI_MANG = 'KET_NOI_MANG', 'Kết nối mạng / Dịch vụ ngoại vi'

    class TrangThaiChoices(models.TextChoices):
        CHO_XU_LY = 'CHO_XU_LY', 'Chờ thử lại'
        DANG_THU_LAI = 'DANG_THU_LAI', 'Đang thử lại'
        THANH_CONG = 'THANH_CONG', 'Thành công (Đã khắc phục)'
        THAT_BAI = 'THAT_BAI', 'Thất bại (Cần can thiệp)'
        DA_HUY = 'DA_HUY', 'Đã hủy bỏ'

    NgoaiLeID = models.AutoField(primary_key=True)
    LoaiNgoaiLe = models.CharField(max_length=50, choices=LoaiNgoaiLeChoices.choices, default=LoaiNgoaiLeChoices.GUI_EMAIL, db_index=True)
    TieuDe = models.CharField(max_length=255)
    MoTaLoi = models.TextField()
    ChiTietNgoaiLe = models.TextField(null=True, blank=True)
    DuLieuPayload = models.JSONField(default=dict, help_text="Dữ liệu ngữ cảnh để thực thi lại tác vụ")
    SoLanThuLai = models.IntegerField(default=0)
    SoLanToiDa = models.IntegerField(default=3)
    TrangThai = models.CharField(max_length=30, choices=TrangThaiChoices.choices, default=TrangThaiChoices.CHO_XU_LY, db_index=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.SET_NULL, null=True, blank=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.SET_NULL, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    NgayTao = models.DateTimeField(auto_now_add=True, db_index=True)
    NgayThuLaiCuoi = models.DateTimeField(null=True, blank=True)
    GhiChuKhacPhuc = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Ngoại lệ và Hàng đợi thử lại"
        ordering = ['-NgayTao']

    def __str__(self):
        return f"[{self.LoaiNgoaiLe}][{self.TrangThai}] {self.TieuDe} (Thử lại: {self.SoLanThuLai}/{self.SoLanToiDa})"
