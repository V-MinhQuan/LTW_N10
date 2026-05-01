from django.db import models
from django.contrib.auth.models import AbstractUser

class VaiTro(models.Model):
    VaiTroID = models.AutoField(primary_key=True)
    ChucVu = models.CharField(max_length=50)

    def __str__(self):
        return self.ChucVu

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

    def is_giam_doc(self):
        return self.role_name == "Tổng giám đốc"

    def is_it_head(self):
        return self.role_name == "Trưởng phòng IT"

    def is_department_head(self):
        return self.role_name and self.role_name.startswith("Trưởng phòng") and not self.is_it_head()

    def is_nhan_vien(self):
        return self.role_name and self.role_name.startswith("Nhân viên")

    def can_approve(self):
        # Trưởng phòng IT không có quyền phê duyệt
        if self.is_it_head():
            return False
        return self.is_giam_doc() or self.is_department_head()

    def can_publish(self):
        # Trưởng phòng IT không có quyền phát hành
        if self.is_it_head():
            return False
        return self.is_giam_doc() or self.is_department_head()

    def can_manage_users_and_units(self):
        # Trưởng phòng các phòng không có quyền quản lý người dùng, đơn vị
        if self.is_department_head():
            return False
        # Giám đốc và IT Head có quyền này
        return self.is_giam_doc() or self.is_it_head()

    def can_perform_action(self, action, obj=None):
        if self.is_giam_doc():
            return True
        
        # Nếu thao tác với một đối tượng cụ thể (Văn bản)
        if obj and action in ['xem', 'sua', 'xoa']:
            # Trưởng phòng: Chỉ được thao tác văn bản thuộc phòng mình
            if self.is_department_head():
                if hasattr(obj, 'DonViTrongID') and obj.DonViTrongID:
                    # So sánh trực tiếp qua ID hoặc Object
                    if obj.DonViTrongID != self.PhongBan:
                        return False
                return True

            # Nhân viên: Chỉ thao tác văn bản của mình tạo hoặc được phân công/chuyển tiếp
            if self.is_nhan_vien():
                # 1. Kiểm tra người tạo
                if hasattr(obj, 'UserID') and obj.UserID == self:
                    return True
                # 2. Kiểm tra phân công/chuyển tiếp
                from .models import PhanCong, ChuyenTiep
                is_assigned = False
                if hasattr(obj, 'VanBanDenID'):
                    is_assigned = PhanCong.objects.filter(VanBanDenID=obj, UserID=self).exists() or \
                                  ChuyenTiep.objects.filter(VanBanDenID=obj, UserID=self).exists()
                elif hasattr(obj, 'VanBanDiID'):
                    is_assigned = PhanCong.objects.filter(VanBanDiID=obj, UserID=self).exists() or \
                                  ChuyenTiep.objects.filter(VanBanDiID=obj, UserID=self).exists()
                
                return is_assigned

        if action in ['phe_duyet', 'phat_hanh']:
            return self.can_approve() and self.can_publish()
            
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

    VanBanDenID = models.AutoField(primary_key=True)
    DonViNgoaiID = models.ForeignKey(DonViBenNgoai, on_delete=models.CASCADE)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    SoKyHieu = models.CharField(max_length=50)
    NgayBanHanh = models.DateTimeField(null=True, blank=True)
    NgayNhan = models.DateTimeField(null=True, blank=True)
    LoaiVanBan = models.CharField(max_length=50, null=True, blank=True)
    TrichYeu = models.CharField(max_length=255, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DANG_XU_LY)
    DonViTrongID = models.ForeignKey(DonViBenTrong, on_delete=models.SET_NULL, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DANG_XU_LY, db_index=True)
    NgayHoanThanh = models.DateTimeField(null=True, blank=True)
    TepDinhKem = models.FileField(upload_to='den/%Y/%m/', null=True, blank=True)

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

    VanBanDiID = models.AutoField(primary_key=True)
    DonViTrongID = models.ForeignKey(DonViBenTrong, on_delete=models.CASCADE, null=True, blank=True)
    DonViNgoaiID = models.ForeignKey(DonViBenNgoai, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    SoKyHieu = models.CharField(max_length=50, db_index=True)
    NgayBanHanh = models.DateTimeField(null=True, blank=True, db_index=True)
    LoaiVanBan = models.CharField(max_length=50, null=True, blank=True)
    TrichYeu = models.CharField(max_length=255, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DU_THAO, db_index=True)
    TepDinhKem = models.FileField(upload_to='di/%Y/%m/', null=True, blank=True)

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
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NgayPhanCong = models.DateTimeField(null=True, blank=True)
    HanXuLy = models.DateTimeField(null=True, blank=True, db_index=True)
    MucDoUuTien = models.CharField(max_length=50, null=True, blank=True)
    TrangThaiXuLy = models.CharField(max_length=50, choices=TrangThaiXuLyChoices.choices, null=True, blank=True, db_index=True)
    GhiChu = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Phân công"

class ChuyenTiep(models.Model):
    ChuyenTiepID = models.AutoField(primary_key=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NgayChuyenTiep = models.DateTimeField(null=True, blank=True)
    NgayBatDau = models.DateTimeField(null=True, blank=True)
    NgayHetHan = models.DateTimeField(null=True, blank=True)
    MucDoUuTien = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Chuyển tiếp"

class LichSuHoatDong(models.Model):
    LichSuID = models.AutoField(primary_key=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    LoaiDoiTuong = models.CharField(max_length=50, null=True, blank=True)
    DoiTuongID = models.IntegerField(null=True, blank=True)
    HanhDong = models.CharField(max_length=50, null=True, blank=True)
    NoiDungThayDoi = models.TextField(null=True, blank=True)
    TrangThaiCu = models.CharField(max_length=50, null=True, blank=True)
    TrangThaiMoi = models.CharField(max_length=50, null=True, blank=True)
    ThoiGianCapNhat = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Lịch sử hoạt động"

class BaoCao(models.Model):
    class LoaiBaoCaoChoices(models.TextChoices):
        TUAN = 'TUAN', 'Báo cáo tuần'
        THANG = 'THANG', 'Báo cáo tháng'
        PHAN_HOI = 'PHAN_HOI', 'Phản hồi'

    PhanHoiID = models.AutoField(primary_key=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NgayBaoCao = models.DateTimeField(null=True, blank=True)
    LoaiBaoCao = models.CharField(max_length=50, choices=LoaiBaoCaoChoices.choices, null=True, blank=True)
    GhiChu = models.CharField(max_length=255, null=True, blank=True)

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
