import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from web.models import (
    VaiTro, UserAccount, DonViBenTrong, DonViBenNgoai,
    VanBanDen, VanBanDi, PhanCong, ChuyenTiep,
    LichSuHoatDong, BaoCao, PheDuyet, PhatHanh, Butphe
)

class Command(BaseCommand):
    help = 'Tạo dữ liệu mẫu cho hệ thống quản lý văn bản công ty du lịch'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Đang bắt đầu tạo dữ liệu mẫu...'))

        # 1. Tạo Vai Trò
        chuc_vus = [
            'Giám đốc', 'Phó Giám đốc', 'Trưởng phòng Điều hành tour', 
            'Trưởng phòng Kế toán', 'Trưởng phòng Marketing', 
            'Nhân viên Điều hành tour', 'Nhân viên Kinh doanh', 
            'Kế toán viên', 'Nhân viên Marketing', 'Văn thư',
            'Nhân viên Sales', 'Trưởng phòng Nhân sự', 'Nhân viên Nhân sự',
            'Hướng dẫn viên', 'Cộng tác viên'
        ]
        roles = []
        for cv in chuc_vus:
            role, _ = VaiTro.objects.get_or_create(ChucVu=cv)
            roles.append(role)
        self.stdout.write(f'Đã tạo {len(roles)} vai trò.')

        # 2. Tạo Đơn vị bên trong
        don_vi_trong_names = [
            'Ban Giám đốc', 'Phòng Điều hành tour', 'Phòng Kế toán - Tài chính',
            'Phòng Marketing & Sales', 'Phòng Nhân sự', 'Phòng Pháp chế',
            'Phòng Công nghệ thông tin', 'Trung tâm lữ hành quốc tế',
            'Trung tâm lữ hành nội địa', 'Phòng Hướng dẫn viên'
        ]
        dvis_trong = []
        for name in don_vi_trong_names:
            dvi = DonViBenTrong.objects.create(
                TenDonVi=name,
                DiaChi='Số 123, Đường Du Lịch, Quận 1, TP. HCM',
                SoDienThoai='028-1234-5678',
                Email=f'{name.lower().replace(" ", "")}@travelco.vn'
            )
            dvis_trong.append(dvi)
        self.stdout.write(f'Đã tạo {len(dvis_trong)} đơn vị nội bộ.')

        # 3. Tạo Đơn vị bên ngoài
        don_vi_ngoai_names = [
            'Vietnam Airlines', 'Vietjet Air', 'Bamboo Airways', 'Khách sạn Daewoo Hanoi',
            'Rex Hotel Saigon', 'Saigontourist Group', 'Vietravel', 'Sở Du lịch TP. HCM',
            'Cục Quản lý Xuất nhập cảnh', 'Công ty Bảo hiểm Bảo Việt', 'Nhà hàng Ngon', 
            'Vinpearl Nha Trang', 'InterContinental Danang', 'Sun World Ba Na Hills',
            'Công ty Vận tải Thành Công', 'Tổng cục Du lịch Viet Nam', 'Đại sứ quán Thái Lan',
            'Lãnh sự quán Hàn Quốc', 'Vinasun Taxi', 'Grab Vietnam'
        ]
        dvis_ngoai = []
        for name in don_vi_ngoai_names:
            dvi = DonViBenNgoai.objects.create(
                TenDonVi=name,
                DiaChi=f'Số {random.randint(1, 500)}, Đường ABC, TP. {random.choice(["Hà Nội", "Hồ Chí Minh", "Đà Nẵng"])}',
                SoDienThoai=f'09{random.randint(10000000, 99999999)}',
                Email=f'contact@{name.lower().replace(" ", "")}.com'
            )
            dvis_ngoai.append(dvi)
        self.stdout.write(f'Đã tạo {len(dvis_ngoai)} đơn vị bên ngoài.')

        # 4. Tạo Người dùng (UserAccount)
        ho_names = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng']
        dem_names = ['Văn', 'Thị', 'Đăng', 'Minh', 'Hồng', 'Thanh', 'Tuấn', 'Quang', 'Anh', 'Ngọc']
        ten_names = ['Hùng', 'Lan', 'Dũng', 'Hương', 'Nam', 'An', 'Bình', 'Hòa', 'Linh', 'Cường']

        users = []
        for i in range(20):
            fullname = f'{random.choice(ho_names)} {random.choice(dem_names)} {random.choice(ten_names)}'
            username = f'user{i+1}'
            user = UserAccount.objects.create_user(
                username=username,
                password='password123',
                email=f'{username}@travelco.vn',
                HoTen=fullname,
                SoDienThoai=f'090{random.randint(1000000, 9999999)}',
                VaiTroID=random.choice(roles),
                TrangThai=True
            )
            users.append(user)
        self.stdout.write(f'Đã tạo {len(users)} người dùng.')

        # Helper for dates
        def random_date(start_days_ago=365):
            return timezone.now() - timedelta(days=random.randint(0, start_days_ago), hours=random.randint(0, 23))

        # 5. Tạo Văn Bản Đến (100)
        loai_vbs = ['Hợp đồng', 'Công văn', 'Tờ trình', 'Quyết định', 'Báo cáo', 'Thông báo', 'Hợp đồng đại lý']
        trich_ycu_list = [
            'Về việc đặt chỗ vé máy bay đoàn khách đi Thái Lan tháng 5',
            'Về việc ký kết hợp đồng tour du lịch hè 2024 tại Nha Trang',
            'Thông báo về việc thay đổi chính sách giá phòng tại Vinpearl',
            'Yêu cầu thanh toán tiền tour đoàn Công ty Samsung tháng 3',
            'Công văn phối hợp tổ chức sự kiện Team Building tại Đà Nẵng',
            'Báo cáo tình hình kinh doanh quý 1 năm 2026',
            'Tờ trình xin phê duyệt kế hoạch khảo sát tour mới tại Nhật Bản',
            'Thông báo của Sở Du lịch về việc cấp thẻ Hướng dẫn viên du lịch',
            'Hợp đồng cung cấp dịch vụ vận chuyển hành khách du lịch năm 2026'
        ]

        vb_den_list = []
        for i in range(100):
            vb = VanBanDen.objects.create(
                DonViNgoaiID=random.choice(dvis_ngoai),
                UserID=random.choice(users),
                SoKyHieu=f'{random.randint(100, 999)}/{random.choice(["QD", "CV", "HD", "TT"])}-DL',
                NgayBanHanh=random_date(),
                NgayNhan=random_date(),
                LoaiVanBan=random.choice(loai_vbs),
                TrichYeu=random.choice(trich_ycu_list),
                TrangThai=random.choice(VanBanDen.TrangThaiChoices.values)
            )
            vb_den_list.append(vb)
        self.stdout.write(f'Đã tạo {len(vb_den_list)} văn bản đến.')

        # 6. Tạo Văn Bản Đi (100)
        vb_di_list = []
        for i in range(100):
            vb = VanBanDi.objects.create(
                DonViTrongID=random.choice(dvis_trong),
                DonViNgoaiID=random.choice(dvis_ngoai),
                UserID=random.choice(users),
                SoKyHieu=f'{random.randint(100, 999)}/{random.choice(["DL", "KT", "DH"])}-VBDI',
                NgayBanHanh=random_date(),
                LoaiVanBan=random.choice(loai_vbs),
                TrichYeu=random.choice(trich_ycu_list),
                TrangThai=random.choice(VanBanDi.TrangThaiChoices.values)
            )
            vb_di_list.append(vb)
        self.stdout.write(f'Đã tạo {len(vb_di_list)} văn bản đi.')

        # 7. Tạo Phân Công (100)
        for i in range(100):
            den_vb = random.choice(vb_den_list) if random.random() > 0.5 else None
            di_vb = random.choice(vb_di_list) if not den_vb else None
            PhanCong.objects.create(
                VanBanDenID=den_vb,
                VanBanDiID=di_vb,
                UserID=random.choice(users),
                NgayPhanCong=random_date(30),
                HanXuLy=random_date(0) + timedelta(days=7),
                MucDoUuTien=random.choice(['Thường', 'Gấp', 'Hỏa tốc']),
                TrangThaiXuLy=random.choice(['Đang xử lý', 'Hoàn thành', 'Chưa xử lý']),
                GhiChu='Xử lý gấp hợp đồng này để kịp tiến độ đặt phòng'
            )
        self.stdout.write('Đã tạo 100 phân công.')

        # 8. Tạo Chuyển Tiếp (100)
        for i in range(100):
            ChuyenTiep.objects.create(
                VanBanDenID=random.choice(vb_den_list),
                VanBanDiID=random.choice(vb_di_list),
                UserID=random.choice(users),
                NgayChuyenTiep=random_date(30),
                NgayBatDau=random_date(30),
                NgayHetHan=random_date(0) + timedelta(days=10),
                MucDoUuTien=random.choice(['Thường', 'Gấp'])
            )
        self.stdout.write('Đã tạo 100 chuyển tiếp.')

        # 9. Tạo Lịch Sử Hoạt Động (100)
        hanh_dongs = ['Thêm mới', 'Chỉnh sửa', 'Cập nhật trạng thái', 'Xóa', 'Phê duyệt', 'Phát hành']
        for i in range(100):
            LichSuHoatDong.objects.create(
                UserID=random.choice(users),
                LoaiDoiTuong=random.choice(['VanBanDen', 'VanBanDi', 'UserAccount']),
                DoiTuongID=random.randint(1, 100),
                HanhDong=random.choice(hanh_dongs),
                NoiDungThayDoi='Cập nhật thông tin chi tiết của bản ghi',
                TrangThaiCu='Cũ',
                TrangThaiMoi='Mới'
            )
        self.stdout.write('Đã tạo 100 lịch sử hoạt động.')

        # 10. Tạo Báo Cáo (100)
        for i in range(100):
            BaoCao.objects.create(
                VanBanDiID=random.choice(vb_di_list),
                VanBanDenID=random.choice(vb_den_list),
                UserID=random.choice(users),
                NgayBaoCao=random_date(60),
                LoaiBaoCao=random.choice(BaoCao.LoaiBaoCaoChoices.values),
                GhiChu='Báo cáo kết quả xử lý tour đoàn tháng vừa qua'
            )
        self.stdout.write('Đã tạo 100 báo cáo.')

        # 11. Tạo Phê Duyệt (100)
        for i in range(100):
            PheDuyet.objects.create(
                VanBanDiID=random.choice(vb_di_list),
                UserID=random.choice(users),
                NgayPheDuyet=random_date(30),
                TrangThaiDuyet=random.choice([True, False]),
                ChuKySo='SIGNED_TOKEN_' + str(random.randint(1000, 9999)),
                GhiChu='Phê duyệt tờ trình xin kinh phí marketing hè 2026'
            )
        self.stdout.write('Đã tạo 100 phê duyệt.')

        # 12. Tạo Phát Hành (100)
        for i in range(100):
            PhatHanh.objects.create(
                VanBanDiID=random.choice(vb_di_list),
                UserID=random.choice(users),
                TieuDe=f'Phát hành văn bản số {random.randint(1, 1000)} - Tour {random.choice(["Nha Trang", "Da Lat", "Phu Quoc"])}',
                TrangThai='Đã phát hành',
                NgayPhatHanh=random_date(10)
            )
        self.stdout.write('Đã tạo 100 phát hành.')

        # 13. Tạo Bút Phê (100)
        for i in range(100):
            Butphe.objects.create(
                VanBanDiID=random.choice(vb_di_list),
                UserID=random.choice(users),
                NoiDung=random.choice([
                    'Đồng ý triển khai tour này.',
                    'Chuyển phòng kế toán kiểm tra lại ngân sách.',
                    'Cần bổ sung thêm thông tin về khách sạn 5 sao.',
                    'Giao phòng điều hành thực hiện ngay trong tuần.',
                    'Tạm hoãn do tình hình thời tiết không thuận lợi.'
                ]),
                NgayButPhe=random_date(5),
                MucDoKhan=random.choice([True, False])
            )
        self.stdout.write('Đã tạo 100 bút phê.')

        self.stdout.write(self.style.SUCCESS('Tất cả dữ liệu mẫu đã được tạo thành công!'))
