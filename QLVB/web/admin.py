from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    VaiTro, UserAccount, DonViBenTrong, DonViBenNgoai,
    VanBanDen, VanBanDi, PhanCong, ChuyenTiep,
    LichSuHoatDong, BaoCao, PheDuyet, PhatHanh, Butphe
)

@admin.register(UserAccount)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Thông tin bổ sung', {'fields': ('HoTen', 'SoDienThoai', 'NgaySinh', 'GioiTinh', 'VaiTroID', 'TrangThai')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Thông tin bổ sung', {'fields': ('HoTen', 'SoDienThoai', 'NgaySinh', 'GioiTinh', 'VaiTroID', 'TrangThai')}),
    )
    # Thêm NgaySinh vào danh sách hiển thị cho dễ nhìn
    list_display = ('username', 'HoTen', 'NgaySinh', 'SoDienThoai', 'is_staff')

@admin.register(VaiTro)
class VaiTroAdmin(admin.ModelAdmin):
    list_display = ('VaiTroID', 'ChucVu')

@admin.register(DonViBenTrong)
class DonViBenTrongAdmin(admin.ModelAdmin):
    list_display = ('TenDonVi', 'SoDienThoai', 'NguoiLienHe')

@admin.register(DonViBenNgoai)
class DonViBenNgoaiAdmin(admin.ModelAdmin):
    list_display = ('TenDonVi', 'SoDienThoai', 'NguoiLienHe')

@admin.register(VanBanDen)
class VanBanDenAdmin(admin.ModelAdmin):
    list_display = ('SoKyHieu', 'NgayBanHanh', 'NgayNhan', 'TrangThai')
    list_filter = ('TrangThai', 'LoaiVanBan')

@admin.register(VanBanDi)
class VanBanDiAdmin(admin.ModelAdmin):
    list_display = ('SoKyHieu', 'NgayBanHanh', 'TrangThai')
    list_filter = ('TrangThai', 'LoaiVanBan')

admin.site.register(PhanCong)
admin.site.register(ChuyenTiep)
admin.site.register(LichSuHoatDong)
admin.site.register(BaoCao)
admin.site.register(PheDuyet)
admin.site.register(PhatHanh)
admin.site.register(Butphe)
