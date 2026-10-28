# 📂 Hệ thống Quản lý Văn bản & Điều hành - Vietasia Travel

Hệ thống quản lý văn bản đi, văn bản đến và xử lý văn bản điều hành, được thiết kế chuyên biệt cho nhu cầu quản trị văn bản của Vietasia Travel.

## 🌟 Tính năng chính

### 1. Quản lý Văn bản Đến
- Tiếp nhận, lưu trữ và quản lý thông tin văn bản từ các đơn vị bên ngoài hoặc nội bộ.
- Đính kèm tệp tin tài liệu gốc.
- Chuyển tiếp văn bản cho các phòng ban liên quan để xử lý.

### 2. Quản lý Văn bản Đi
- Quy trình phê duyệt chặt chẽ: Dự thảo → Gửi phê duyệt → Phê duyệt → Phát hành.
- Phát hành linh hoạt: Có thể phát hành cho từng đơn vị cụ thể hoặc phát hành toàn hệ thống.
- Tự động đồng bộ sang màn hình Xử lý văn bản điều hành sau khi phát hành thành công.

### 3. Xử lý Văn bản Điều hành
- Tập trung các văn bản cần xử lý cho từng cá nhân/phòng ban.
- Phân công nhiệm vụ: Trưởng phòng có quyền phân công văn bản cho nhân viên, quy định hạn xử lý và mức độ ưu tiên.
- Theo dõi trạng thái xử lý: Mới, Đang xử lý, Hoàn thành, Quá hạn.

### 4. Quản lý Người dùng & Phân quyền
- Phân quyền theo vai trò: Tổng giám đốc, Trưởng phòng IT, Trưởng phòng chuyên môn, Nhân viên.
- Chế độ chỉnh sửa thông tin:
  - Giám đốc & Trưởng phòng IT: Toàn quyền chỉnh sửa hệ thống.
  - Nhân viên: Chỉ được tự sửa Email và Số điện thoại cá nhân.
- Bảo mật: Chặn vô hiệu hóa tài khoản nếu người dùng đó đang còn công việc chưa hoàn thành.

### 5. Quản lý Đơn vị
- Quản lý danh sách Đơn vị bên trong (Phòng ban) và Đơn vị bên ngoài (Đối tác/Cơ quan).
- Chặn xóa/vô hiệu hóa đơn vị nếu đang có văn bản đang trong quá trình xử lý liên quan đến đơn vị đó.

## 🛠 Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Backend | Python (Django Framework) |
| Frontend | HTML5, CSS, JavaScript |
| Database | PostgreSQL |
| BaaS | Supabase |
| UI/UX | Giao diện hiện đại, tối ưu cho trải nghiệm người dùng văn phòng |

---

## 📊 Cấu trúc Cơ sở dữ liệu

Hệ thống sử dụng **PostgreSQL**, được xây dựng trên nền tảng **Django ORM**. Tổng cộng gồm **22 bảng** với **27 quan hệ khóa ngoại**.

### Sơ đồ quan hệ tổng quan

```
web_donvibentrong (Phong ban noi bo)
 ├── web_vaitro.PhongBan_id
 ├── web_useraccount.PhongBan_id
 ├── web_vanbanden.DonViTrongID_id
 └── web_vanbandi.DonViTrongID_id

web_donvibenngoai (Don vi ben ngoai)
 ├── web_vanbanden.DonViNgoaiID_id
 └── web_vanbandi.DonViNgoaiID_id

web_useraccount (Nguoi dung)
 ├── web_vanbanden.UserID_id          -> Nguoi tiep nhan
 ├── web_vanbandi.UserID_id           -> Nguoi soan thao
 ├── web_vanbandi.NguoiGui_id         -> Nguoi gui
 ├── web_phancong.UserID_id           -> Nguoi duoc phan cong
 ├── web_chuyentiep.UserID_id         -> Nguoi nhan chuyen tiep
 ├── web_pheduyet.UserID_id           -> Nguoi phe duyet
 ├── web_phathanh.UserID_id           -> Nguoi phat hanh
 ├── web_butphe.UserID_id             -> Nguoi but phe
 ├── web_baocao.UserID_id             -> Nguoi bao cao
 ├── web_baocao.RecipientID_id        -> Nguoi nhan bao cao
 └── web_lichsuhoatdong.UserID_id     -> Nguoi thuc hien

web_vanbanden (Van ban den)
 ├── web_phancong.VanBanDenID_id
 ├── web_chuyentiep.VanBanDenID_id
 └── web_baocao.VanBanDenID_id

web_vanbandi (Van ban di)
 ├── web_vanbanden.VanBanDiID_id      -> Lien ket VB den - VB di
 ├── web_phancong.VanBanDiID_id
 ├── web_chuyentiep.VanBanDiID_id
 ├── web_pheduyet.VanBanDiID_id
 ├── web_phathanh.VanBanDiID_id
 ├── web_butphe.VanBanDiID_id
 └── web_baocao.VanBanDiID_id
```

---

### Bảng hệ thống Django

| Bảng | Mô tả |
|------|--------|
| `auth_group` | Nhóm người dùng để phân quyền |
| `auth_group_permissions` | Bảng trung gian liên kết nhóm với quyền (M2M) |
| `auth_permission` | Danh sách các quyền hệ thống |
| `django_admin_log` | Nhật ký thao tác trên trang quản trị |
| `django_content_type` | Đăng ký các model trong hệ thống |
| `django_migrations` | Lịch sử các migration đã chạy |
| `django_session` | Quản lý phiên đăng nhập |

---

### Bảng nghiệp vụ ứng dụng

#### `web_useraccount` — Tài khoản người dùng

Kế thừa từ `AbstractUser` của Django, mở rộng thêm các trường nghiệp vụ.

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `UserID` | `integer` (auto) | **PK** | Mã người dùng |
| `username` | `varchar` | UNIQUE, NOT NULL | Tên đăng nhập |
| `password` | `varchar` | NOT NULL | Mật khẩu (đã mã hóa) |
| `HoTen` | `varchar` | NOT NULL | Họ và tên |
| `email` | `varchar` | NOT NULL | Email |
| `SoDienThoai` | `varchar` | NOT NULL | Số điện thoại |
| `GioiTinh` | `varchar` | — | Giới tính |
| `NgaySinh` | `date` | — | Ngày sinh |
| `VaiTroID_id` | `integer` | **FK** → `web_vaitro` | Vai trò / chức vụ |
| `PhongBan_id` | `integer` | **FK** → `web_donvibentrong` | Phòng ban trực thuộc |
| `is_superuser` | `boolean` | NOT NULL | Quyền super admin |
| `is_staff` | `boolean` | NOT NULL | Quyền truy cập admin site |
| `is_active` | `boolean` | NOT NULL | Trạng thái hoạt động |
| `TrangThai` | `boolean` | NOT NULL | Trạng thái nghiệp vụ |
| `trang_thai` | `varchar` | NOT NULL, DEFAULT `'ACTIVE'` | Trạng thái (text) |
| `SoThuTu` | `integer` | — | Số thứ tự hiển thị |
| `date_joined` | `timestamptz` | NOT NULL | Ngày tạo tài khoản |
| `last_login` | `timestamptz` | — | Lần đăng nhập cuối |
| `created_at` | `timestamptz` | DEFAULT `now()` | Thời điểm tạo |
| `updated_at` | `timestamptz` | DEFAULT `now()` | Thời điểm cập nhật |

> **Bảng trung gian:**
> - `web_useraccount_groups` — Liên kết User ↔ Group (M2M)
> - `web_useraccount_user_permissions` — Liên kết User ↔ Permission (M2M)

---

#### `web_vaitro` — Vai trò / Chức vụ

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `VaiTroID` | `integer` (auto) | **PK** | Mã vai trò |
| `ChucVu` | `varchar` | NOT NULL | Tên chức vụ |
| `PhongBan_id` | `integer` | **FK** → `web_donvibentrong` | Phòng ban tương ứng |

---

#### `web_donvibentrong` — Đơn vị bên trong (Phòng ban nội bộ)

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `DonViTrongID` | `integer` (auto) | **PK** | Mã đơn vị nội bộ |
| `TenDonVi` | `varchar` | NOT NULL | Tên đơn vị |
| `DiaChi` | `varchar` | — | Địa chỉ |
| `SoDienThoai` | `varchar` | — | Số điện thoại |
| `NguoiLienHe` | `varchar` | — | Người liên hệ |
| `Email` | `varchar` | — | Email |
| `SoThuTu` | `integer` | — | Số thứ tự hiển thị |
| `trang_thai` | `varchar` | DEFAULT `'ACTIVE'` | Trạng thái |
| `created_at` | `timestamptz` | DEFAULT `CURRENT_TIMESTAMP` | Thời điểm tạo |
| `updated_at` | `timestamptz` | DEFAULT `CURRENT_TIMESTAMP` | Thời điểm cập nhật |

---

#### `web_donvibenngoai` — Đơn vị bên ngoài

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `DonViNgoaiID` | `integer` (auto) | **PK** | Mã đơn vị ngoài |
| `TenDonVi` | `varchar` | NOT NULL | Tên đơn vị |
| `DiaChi` | `varchar` | — | Địa chỉ |
| `SoDienThoai` | `varchar` | — | Số điện thoại |
| `NguoiLienHe` | `varchar` | — | Người liên hệ |
| `Email` | `varchar` | — | Email |
| `SoThuTu` | `integer` | — | Số thứ tự hiển thị |
| `trang_thai` | `varchar` | NOT NULL, DEFAULT `'ACTIVE'` | Trạng thái |
| `created_at` | `timestamptz` | DEFAULT `now()` | Thời điểm tạo |
| `updated_at` | `timestamptz` | DEFAULT `now()` | Thời điểm cập nhật |

---

#### `web_vanbanden` — Văn bản đến

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `VanBanDenID` | `integer` (auto) | **PK** | Mã văn bản đến |
| `SoKyHieu` | `varchar` | NOT NULL | Số ký hiệu văn bản |
| `NgayBanHanh` | `timestamptz` | — | Ngày ban hành |
| `NgayNhan` | `timestamptz` | — | Ngày nhận văn bản |
| `NgayVanBan` | `timestamptz` | — | Ngày văn bản |
| `NgayHoanThanh` | `timestamptz` | — | Ngày hoàn thành xử lý |
| `LoaiVanBan` | `varchar` | — | Loại văn bản |
| `TrichYeu` | `varchar` | — | Trích yếu nội dung |
| `TrangThai` | `varchar` | NOT NULL | Trạng thái xử lý |
| `TepDinhKem` | `varchar` | — | Đường dẫn tệp đính kèm |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người tiếp nhận |
| `DonViNgoaiID_id` | `integer` | **FK** → `web_donvibenngoai` | Đơn vị gửi (bên ngoài) |
| `DonViTrongID_id` | `integer` | **FK** → `web_donvibentrong` | Đơn vị gửi (bên trong) |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi liên kết |

---

#### `web_vanbandi` — Văn bản đi

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `VanBanDiID` | `integer` (auto) | **PK** | Mã văn bản đi |
| `SoKyHieu` | `varchar` | NOT NULL | Số ký hiệu văn bản |
| `NgayBanHanh` | `timestamptz` | — | Ngày ban hành |
| `NgayGuiPheDuyet` | `timestamptz` | — | Ngày gửi phê duyệt |
| `NgayPheDuyet` | `timestamptz` | — | Ngày được phê duyệt |
| `NgayPhatHanh` | `timestamptz` | — | Ngày phát hành |
| `LoaiVanBan` | `varchar` | — | Loại văn bản |
| `TrichYeu` | `varchar` | — | Trích yếu nội dung |
| `TrangThai` | `varchar` | NOT NULL | Trạng thái xử lý |
| `TepDinhKem` | `varchar` | — | Đường dẫn tệp đính kèm |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người soạn thảo |
| `NguoiGui_id` | `integer` | **FK** → `web_useraccount` | Người gửi |
| `DonViNgoaiID_id` | `integer` | **FK** → `web_donvibenngoai` | Đơn vị nhận (bên ngoài) |
| `DonViTrongID_id` | `integer` | **FK** → `web_donvibentrong` | Đơn vị soạn (bên trong) |

---

#### `web_phancong` — Phân công xử lý

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `PhanCongID` | `integer` (auto) | **PK** | Mã phân công |
| `NgayPhanCong` | `timestamptz` | — | Ngày phân công |
| `HanXuLy` | `timestamptz` | — | Hạn xử lý |
| `MucDoUuTien` | `varchar` | — | Mức độ ưu tiên |
| `TrangThaiXuLy` | `varchar` | — | Trạng thái xử lý |
| `GhiChu` | `varchar` | — | Ghi chú |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người được phân công |
| `VanBanDenID_id` | `integer` | **FK** → `web_vanbanden` | Văn bản đến liên quan |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi liên quan |

---

#### `web_chuyentiep` — Chuyển tiếp văn bản

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `ChuyenTiepID` | `integer` (auto) | **PK** | Mã chuyển tiếp |
| `NgayChuyenTiep` | `timestamptz` | — | Ngày chuyển tiếp |
| `NgayBatDau` | `timestamptz` | — | Ngày bắt đầu |
| `NgayHetHan` | `timestamptz` | — | Ngày hết hạn |
| `MucDoUuTien` | `varchar` | — | Mức độ ưu tiên |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người nhận chuyển tiếp |
| `VanBanDenID_id` | `integer` | **FK** → `web_vanbanden` | Văn bản đến |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi |

---

#### `web_pheduyet` — Phê duyệt văn bản đi

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `PheDuyetID` | `integer` (auto) | **PK** | Mã phê duyệt |
| `NgayPheDuyet` | `timestamptz` | — | Ngày phê duyệt |
| `TrangThaiDuyet` | `boolean` | NOT NULL | Trạng thái duyệt (True = Đồng ý) |
| `ChuKySo` | `text` | — | Chữ ký số |
| `GhiChu` | `text` | — | Ghi chú |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người phê duyệt |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi được duyệt |

---

#### `web_phathanh` — Phát hành văn bản đi

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `PhatHanhID` | `integer` (auto) | **PK** | Mã phát hành |
| `TieuDe` | `varchar` | — | Tiêu đề |
| `TrangThai` | `varchar` | — | Trạng thái phát hành |
| `NgayPhatHanh` | `timestamptz` | — | Ngày phát hành |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người phát hành |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi |

---

#### `web_butphe` — Bút phê

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `ButPheID` | `integer` (auto) | **PK** | Mã bút phê |
| `NoiDung` | `varchar` | — | Nội dung bút phê |
| `NgayButPhe` | `timestamptz` | — | Ngày bút phê |
| `MucDoKhan` | `boolean` | NOT NULL | Mức độ khẩn |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người bút phê |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi |

---

#### `web_baocao` — Báo cáo / Phản hồi

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `PhanHoiID` | `integer` (auto) | **PK** | Mã báo cáo |
| `NgayBaoCao` | `timestamptz` | — | Ngày báo cáo |
| `LoaiBaoCao` | `varchar` | — | Loại báo cáo |
| `GhiChu` | `varchar` | — | Ghi chú |
| `HuongXuLy` | `varchar` | — | Hướng xử lý |
| `NoiDungXuLy` | `text` | — | Nội dung xử lý |
| `TrangThai` | `varchar` | NOT NULL | Trạng thái báo cáo |
| `TrangThaiVBCu` | `varchar` | — | Trạng thái VB trước khi báo cáo |
| `ResolvedAt` | `timestamptz` | — | Thời điểm giải quyết |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người báo cáo |
| `RecipientID_id` | `integer` | **FK** → `web_useraccount` | Người nhận báo cáo |
| `VanBanDenID_id` | `integer` | **FK** → `web_vanbanden` | Văn bản đến liên quan |
| `VanBanDiID_id` | `integer` | **FK** → `web_vanbandi` | Văn bản đi liên quan |

---

#### `web_lichsuhoatdong` — Lịch sử hoạt động

| Cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|-----|---------------|-----------|-------|
| `LichSuID` | `integer` (auto) | **PK** | Mã lịch sử |
| `LoaiDoiTuong` | `varchar` | — | Loại đối tượng (VB đến, VB đi,...) |
| `DoiTuongID` | `integer` | — | ID đối tượng liên quan |
| `HanhDong` | `varchar` | — | Hành động thực hiện |
| `NoiDungThayDoi` | `text` | — | Nội dung thay đổi chi tiết |
| `TrangThaiCu` | `varchar` | — | Trạng thái trước |
| `TrangThaiMoi` | `varchar` | — | Trạng thái sau |
| `ThoiGianCapNhat` | `timestamptz` | NOT NULL | Thời gian thực hiện |
| `UserID_id` | `integer` | **FK** → `web_useraccount` | Người thực hiện |

---

### Thống kê

| Chỉ số | Giá trị |
|--------|---------|
| Tổng số bảng | **22** |
| Bảng hệ thống Django | 7 (`auth_*`, `django_*`) |
| Bảng nghiệp vụ chính | 13 (`web_*`) |
| Bảng trung gian (M2M) | 2 (`web_useraccount_groups`, `web_useraccount_user_permissions`) |
| Tổng số quan hệ FK | **27** |
