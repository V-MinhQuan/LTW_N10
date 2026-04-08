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
    TrangThai = models.BooleanField(default=True)

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

    def __str__(self):
        return self.TenDonVi

    class Meta:
        verbose_name_plural = "Đơn vị bên ngoài"

class VanBanDen(models.Model):
    class TrangThaiChoices(models.TextChoices):
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
    DonViTrongID = models.ForeignKey(DonViBenTrong, on_delete=models.CASCADE)
    DonViNgoaiID = models.ForeignKey(DonViBenNgoai, on_delete=models.CASCADE)
    UserID = models.ForeignKey(UserAccount, on_delete=models.SET_NULL, null=True, blank=True)
    SoKyHieu = models.CharField(max_length=50)
    NgayBanHanh = models.DateTimeField(null=True, blank=True)
    LoaiVanBan = models.CharField(max_length=50, null=True, blank=True)
    TrichYeu = models.CharField(max_length=255, null=True, blank=True)
    TrangThai = models.CharField(max_length=50, choices=TrangThaiChoices.choices, default=TrangThaiChoices.DU_THAO)
    TepDinhKem = models.FileField(upload_to='di/%Y/%m/', null=True, blank=True)

    def __str__(self):
        return self.SoKyHieu

    class Meta:
        verbose_name_plural = "Văn bản đi"

class PhanCong(models.Model):
    PhanCongID = models.AutoField(primary_key=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE, null=True, blank=True)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE, null=True, blank=True)
    UserID = models.ForeignKey(UserAccount, on_delete=models.CASCADE)
    NgayPhanCong = models.DateTimeField(null=True, blank=True)
    HanXuLy = models.DateTimeField(null=True, blank=True)
    MucDoUuTien = models.CharField(max_length=50, null=True, blank=True)
    TrangThaiXuLy = models.CharField(max_length=50, null=True, blank=True)
    GhiChu = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Phân công"

class ChuyenTiep(models.Model):
    ChuyenTiepID = models.AutoField(primary_key=True)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE)
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE)
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
    VanBanDiID = models.ForeignKey(VanBanDi, on_delete=models.CASCADE)
    VanBanDenID = models.ForeignKey(VanBanDen, on_delete=models.CASCADE)
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
