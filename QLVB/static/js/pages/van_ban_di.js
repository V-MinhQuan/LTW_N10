function getCookie(name) {
    let v = document.cookie.match('(^|;) ?' + name + '=([^;]*)(;|$)');
    return v ? v[2] : null;
}

function apiPost(url, data, onSuccess) {
    fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success') onSuccess(res);
            else alert('Lỗi: ' + res.message);
        })
        .catch(() => alert('Có lỗi xảy ra, vui lòng thử lại.'));
}

function apiPostForm(url, formData, onSuccess) {
    fetch(url, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: formData
    })
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success') onSuccess(res);
            else alert('Lỗi: ' + res.message);
        })
        .catch(() => alert('Có lỗi xảy ra, vui lòng thử lại.'));
}

function goPage(page) {
    let url = new URL(window.location.href);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}

function openVBD(id) {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'block';
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'flex';
        // Reset form nếu là modal thêm mới
        if (id === 'modalForm') {
            const inputs = modal.querySelectorAll('input, select, textarea');
            inputs.forEach(i => {
                if (i.type !== 'button' && i.type !== 'submit') {
                    i.value = '';
                    if (i.tagName === 'SELECT' && (i.id === 'donViBH' || i.id === 'nguoiSoanThao' || i.id === 'donViNgoai')) {
                        i.selectedIndex = 0;
                        if (i.id === 'nguoiSoanThao') i.innerHTML = '<option value="">--- Chọn người xử lý ---</option>';
                        if (i.id === 'donViBH' || i.id === 'donViNgoai') i.disabled = false;
                    }
                }
            });
            const label = document.getElementById('fileLabel');
            if (label) label.innerHTML = 'Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính';

            // Lấy gợi ý số ký hiệu
            fetch('/api/van-ban-di/goi-y-so-ky-hieu/')
                .then(r => r.json())
                .then(res => {
                    if (res.status === 'success') {
                        document.getElementById('soKyHieu').value = res.suggested;
                    }
                });
        }
    }
}

function closeVBD(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';

    // Kiểm tra xem có còn modal nào đang mở không
    const visibleModals = document.querySelectorAll('.modal-box[style*="display: flex"], .vbd-popup-overlay[style*="display: flex"]');
    if (visibleModals.length === 0) {
        const overlay = document.getElementById('modalOverlay');
        if (overlay) overlay.style.display = 'none';
    }

    if (id === 'historyOverlay') {
        openVBD('modalDetail');
    }
}

window.onclick = function (event) {
    if (event.target.classList.contains('vbd-popup-overlay') || event.target.classList.contains('modal-box')) {
        closeVBD(event.target.id);
    }
    if (event.target.id === 'modalOverlay') {
        closeAllModals();
    }
}



function _renderFile(section, noFileEl, tepDinhKem, showDelete = true) {
    if (tepDinhKem) {
        let fileName = tepDinhKem.split('/').pop();
        let ext = fileName.split('.').pop().toUpperCase();
        section.style.display = 'block';
        noFileEl.style.display = 'none';

        let deleteBtn = showDelete ? `
            <button type="button" style="background:none;border:none;cursor:pointer;color:#888;font-size:16px;padding:4px 8px;" onclick="xoaFileHienCo()">
                <i class="fas fa-trash"></i>
            </button>` : '';

        section.innerHTML = `<div class="vbd-file-item">
            <div class="vbd-file-info">
                <div class="vbd-file-icon">${ext}</div>
                <div class="vbd-file-details">
                    <a class="vbd-file-name" href="/media/${tepDinhKem}" download="${fileName}" onclick="window.open(this.href, '_blank'); return true;">${fileName}</a>
                    <span class="vbd-file-size"></span>
                </div>
            </div>
            ${deleteBtn}
        </div>`;
    } else {
        section.style.display = 'none';
        noFileEl.style.display = 'block';
        section.innerHTML = '';
    }
}

function xoaFileHienCo() {
    let section = document.getElementById('edit_file_section');
    let noFile = document.getElementById('edit_no_file');
    section.innerHTML = '';
    section.style.display = 'none';
    noFile.style.display = 'block';
    // Đánh dấu xóa file để gửi lên server
    document.getElementById('edit_xoa_file').value = '1';
    // Reset input file nếu có
    let fi = document.getElementById('edit_file_input');
    if (fi) fi.value = '';
}

// ---- XEM CHI TIẾT ----
let _detailId = null;

function xemChiTiet(btn) {
    _detailId = btn.closest("tr").dataset.id;
    fetch('/api/van-ban-di/' + _detailId + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            let d = res.data;
            document.getElementById("ct_sokyhieu").value = d.so_ky_hieu;
            document.getElementById("ct_trichyeu").value = d.trich_yeu;
            document.getElementById("ct_donvi").value = (d.don_vi_trong || d.don_vi_ngoai) || 'Chưa xác định';
            document.getElementById("ct_loaivb").value = d.loai_vb;
            document.getElementById("ct_nguoisoan").value = d.nguoi_soan;
            document.getElementById("ct_ngay").value = d.ngay_ban_hanh;
            document.getElementById("ct_trangthai").value = d.trang_thai;
            _renderFile(document.getElementById('ct_file_section'), document.getElementById('ct_no_file'), d.tep_dinh_kem, false);

            // Render lịch sử xử lý
            const historyContainer = document.getElementById('ct_process_history');
            if (historyContainer) {
                historyContainer.innerHTML = '';
                if (d.xu_ly_history && d.xu_ly_history.length > 0) {
                    // Map loại -> icon
                    const iconMap = {
                        'Phân công': 'fas fa-user-plus',
                        'Chuyển tiếp': 'fas fa-share',
                        'Báo cáo': 'fas fa-flag',
                        'Bút phê': 'fas fa-pen-nib',
                    };
                    d.xu_ly_history.forEach(item => {
                        const icon = iconMap[item.type] || 'fas fa-circle';
                        const row = document.createElement('div');
                        row.className = 'vbd-process-row';
                        row.innerHTML = `
                        <div><span class="vbd-process-tag ${item.tag_class}">${item.type}</span></div>
                        <div class="vbd-process-personnel">
                            <div class="vbd-process-personnel-icon">
                                <i class="${icon}"></i> ${item.user}
                            </div>
                            <div class="vbd-process-personnel-sub">Tài khoản: ${item.username}</div>
                        </div>
                        <div>
                            <div class="vbd-process-action-box">${item.action}</div>
                            <div class="vbd-process-time-row"><i class="far fa-clock"></i> ${item.time}</div>
                        </div>
                    `;
                        historyContainer.appendChild(row);
                    });
                } else {
                    historyContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #999;">Chưa có nội dung xử lý văn bản này.</div>';
                }
            }

            openVBD('modalDetail');
        });
}

// ---- THÊM MỚI ----
function _getFormData(trangThai) {
    let fd = new FormData();
    fd.append('so_ky_hieu', document.getElementById('soKyHieu').value);
    fd.append('trich_yeu', document.getElementById('trichYeu').value);
    fd.append('loai_vb', document.getElementById('loaiVB').value);
    fd.append('ngay_ban_hanh', document.getElementById('ngayBanHanh').value || '');
    fd.append('don_vi_trong_id', document.getElementById('donViBH').value);
    fd.append('don_vi_ngoai_id', document.getElementById('donViNgoai') ? document.getElementById('donViNgoai').value : '');
    fd.append('nguoi_soan_id', document.getElementById('nguoiSoanThao').value || '');
    fd.append('trang_thai', trangThai);
    let fileInput = document.getElementById('fileInput');
    if (fileInput && fileInput.files[0]) fd.append('tep_dinh_kem', fileInput.files[0]);
    return fd;
}

function luuDuThao() {
    let fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files[0]) {
        alert('Vui lòng đính kèm tài liệu!');
        return;
    }
    apiPostForm('/api/van-ban-di/them-moi/', _getFormData('DU_THAO'), () => {
        App.showSuccess('Lưu dự thảo thành công', () => {
            window.location.reload();
        });
    });
}

function guiPheDuyet() {
    let fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files[0]) {
        alert('Vui lòng đính kèm tài liệu!');
        return;
    }
    apiPostForm('/api/van-ban-di/them-moi/', _getFormData('CHO_PHE_DUYET'), () => {
        App.showSuccess('Gửi phê duyệt thành công', () => {
            window.location.reload();
        });
    });
}

// ---- SỬA ----
let _editId = null;

function previewEditFile(input) {
    if (!input.files[0]) return;
    let file = input.files[0];
    let ext = file.name.split('.').pop().toUpperCase();
    let section = document.getElementById('edit_file_section');
    let noFile = document.getElementById('edit_no_file');
    section.style.display = 'block';
    noFile.style.display = 'none';
    section.innerHTML = `<div class="vbd-file-item">
        <div class="vbd-file-info">
            <div class="vbd-file-icon">${ext}</div>
            <div class="vbd-file-details">
                <span class="vbd-file-name">${file.name}</span>
                <span class="vbd-file-size">${(file.size / 1024 / 1024).toFixed(2)} MB</span>
            </div>
        </div>
        <button type="button" style="background:none;border:none;cursor:pointer;color:#888;font-size:16px;padding:4px 8px;" onclick="openVBD('popupRemoveFile')">
            <i class="fas fa-trash"></i>
        </button>
    </div>`;
}

function suaVanBan(btn) {
    _editId = btn.closest("tr").dataset.id;
    fetch('/api/van-ban-di/' + _editId + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            let d = res.data;
            document.getElementById("edit_trichyeu").value = d.trich_yeu;
            document.getElementById("edit_sokyhieu").value = d.so_ky_hieu;
            document.getElementById("edit_loaivb").value = d.loai_vb;
            document.getElementById("edit_nguoisoan").value = d.nguoi_soan;

            // Set dropdown đơn vị — tìm theo text hoặc id
            // Set dropdown đơn vị — sử dụng tên cho autocomplete
            document.getElementById("edit_donViBH").value = d.don_vi_trong || '';
            document.getElementById("edit_donViNgoai").value = d.don_vi_ngoai || '';
            if (d.don_vi_trong) {
                // Tìm ID tương ứng với tên để load nhân viên
                let dept = _cachedDonVi.trong.find(i => i.ten === d.don_vi_trong);
                if (dept) loadUsersByDept(dept.id, 'edit_nguoisoan', d.nguoi_soan_id);
            }


            // Map tên hiển thị -> mã
            let ttMap = { 'Dự thảo': 'DU_THAO', 'Chờ phê duyệt': 'CHO_PHE_DUYET', 'Đã phê duyệt': 'DA_PHE_DUYET', 'Đã phát hành': 'DA_PHAT_HANH' };
            document.getElementById("edit_trangthai").value = ttMap[d.trang_thai] || 'DU_THAO';

            let parts = d.ngay_ban_hanh.split("/");
            if (parts.length === 3) document.getElementById("edit_ngay").value = parts[2] + "-" + parts[1] + "-" + parts[0];

            _renderFile(document.getElementById('edit_file_section'), document.getElementById('edit_no_file'), d.tep_dinh_kem);
            document.getElementById('edit_xoa_file').value = '0'; // reset flag
            openVBD('modalEdit');
        });
}

function luuCapNhat() {
    if (!_editId) return;

    let trong = document.getElementById('edit_donViBH').value;
    let ngoai = document.getElementById('edit_donViNgoai').value;
    if (!trong && !ngoai) {
        App.showAlert("Vui lòng chọn đơn vị nhận văn bản!");
        return;
    }

    let fd = new FormData();
    fd.append('so_ky_hieu', document.getElementById('edit_sokyhieu').value);
    fd.append('trich_yeu', document.getElementById('edit_trichyeu').value);
    fd.append('loai_vb', document.getElementById('edit_loaivb').value);
    fd.append('ngay_ban_hanh', document.getElementById('edit_ngay').value || '');
    fd.append('don_vi_trong_id', trong);
    fd.append('don_vi_ngoai_id', ngoai);
    fd.append('nguoi_soan_id', document.getElementById('edit_nguoisoan').value || '');
    fd.append('trang_thai', document.getElementById('edit_trangthai').value);
    fd.append('xoa_file', document.getElementById('edit_xoa_file').value);
    let fileInput = document.getElementById('edit_file_input');
    if (fileInput && fileInput.files[0]) fd.append('tep_dinh_kem', fileInput.files[0]);
    apiPostForm('/api/van-ban-di/' + _editId + '/cap-nhat/', fd, () => {
        App.showSuccess('Cập nhật thành công', () => {
            window.location.reload();
        });
    });
}

function guiPheDuyetCapNhat() {
    if (!_editId) return;
    document.getElementById('edit_trangthai').value = 'CHO_PHE_DUYET';
    luuCapNhat();
}

// ---- XÓA ----
let _xoaId = null;

function xoaVanBan(btn) {
    const id = btn.closest("tr").dataset.id;
    App.confirmDelete("Bạn có chắc chắn muốn xóa văn bản này không?", function () {
        submitXoaVanBan(id);
    });
}

function submitXoaVanBan(id) {
    apiPost('/api/van-ban-di/' + id + '/xoa/', {}, () => {
        App.showSuccess('Xóa thành công', () => {
            window.location.reload();
        });
    });
}

function xacNhanXoaFile() {
    if (!_xoaId) return;
    apiPost('/api/van-ban-di/' + _xoaId + '/xoa/', {}, () => {
        closeVBD('popupRemoveFile');
        window.location.reload();
    });
}

// ---- PHÊ DUYỆT ----
let _pheDuyetId = null;

function pheDuyetVanBan(btn) {
    _pheDuyetId = btn.closest("tr").dataset.id;
    openVBD('popupPheDuyet');
    initSignaturePad();
}

let _isSigning = false;
let _sigCanvas = null;
let _sigCtx = null;

function initSignaturePad() {
    _sigCanvas = document.getElementById('signature-pad');
    if (!_sigCanvas) return;
    _sigCtx = _sigCanvas.getContext('2d');
    _sigCtx.strokeStyle = "#222";
    _sigCtx.lineWidth = 2;
    _sigCtx.lineJoin = "round";
    _sigCtx.lineCap = "round";

    // Mouse events
    _sigCanvas.addEventListener("mousedown", startSign);
    _sigCanvas.addEventListener("mousemove", drawSign);
    _sigCanvas.addEventListener("mouseup", stopSign);
    _sigCanvas.addEventListener("mouseleave", stopSign);

    // Touch events
    _sigCanvas.addEventListener("touchstart", (e) => {
        e.preventDefault();
        startSign(e.touches[0]);
    });
    _sigCanvas.addEventListener("touchmove", (e) => {
        e.preventDefault();
        drawSign(e.touches[0]);
    });
    _sigCanvas.addEventListener("touchend", stopSign);
}

function startSign(e) {
    _isSigning = true;
    _sigCtx.beginPath();
    const pos = _getPos(e);
    _sigCtx.moveTo(pos.x, pos.y);
    document.getElementById('signature-placeholder').style.display = 'none';
}

function drawSign(e) {
    if (!_isSigning) return;
    const pos = _getPos(e);
    _sigCtx.lineTo(pos.x, pos.y);
    _sigCtx.stroke();
}

function stopSign() {
    _isSigning = false;
}

function _getPos(e) {
    const rect = _sigCanvas.getBoundingClientRect();
    const scaleX = _sigCanvas.width / rect.width;
    const scaleY = _sigCanvas.height / rect.height;
    return {
        x: (e.clientX - rect.left) * scaleX,
        y: (e.clientY - rect.top) * scaleY
    };
}

function clearSignature() {
    if (!_sigCanvas) return;
    _sigCtx.clearRect(0, 0, _sigCanvas.width, _sigCanvas.height);
    document.getElementById('signature-placeholder').style.display = 'block';
}

function xacNhanPheDuyet(chap_nhan) {
    if (!_pheDuyetId) return;

    // Kiểm tra nếu chap_nhan = true thì bắt buộc phải ký
    let chuKy = _sigCanvas ? _sigCanvas.toDataURL() : '';
    let isEmpty = true;
    if (_sigCanvas) {
        let blank = document.createElement('canvas');
        blank.width = _sigCanvas.width;
        blank.height = _sigCanvas.height;
        if (_sigCanvas.toDataURL() !== blank.toDataURL()) isEmpty = false;
    }

    if (chap_nhan && isEmpty) {
        App.showAlert("Vui lòng ký tên trước khi phê duyệt.");
        return;
    }

    let data = {
        chap_nhan: chap_nhan,
        ghi_chu: document.getElementById('pd_ghichu') ? document.getElementById('pd_ghichu').value : '',
        chu_ky_so: isEmpty ? '' : chuKy
    };
    apiPost('/api/van-ban-di/' + _pheDuyetId + '/phe-duyet/', data, () => {
        if (chap_nhan) {
            App.showSuccess('Xử lý phê duyệt thành công', () => {
                window.location.reload();
            });
        } else {
            App.showError('Từ chối phê duyệt thành công', () => {
                window.location.reload();
            });
        }
    });
}

// ---- PHÁT HÀNH ----
let _phatHanhId = null;

function phatHanhVanBan(btn) {
    _phatHanhId = btn.closest("tr").dataset.id;
    fetch('/api/van-ban-di/' + _phatHanhId + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            let d = res.data;
            document.getElementById("ph_trichyeu").value = d.trich_yeu;
            if (d.ngay_ban_hanh) {
                let parts = d.ngay_ban_hanh.split("/");
                if (parts.length === 3) {
                    document.getElementById("ph_ngay").value = parts[2] + "-" + parts[1] + "-" + parts[0];
                }
            }
            let ph_phongban = document.getElementById("ph_phongban");
            if (ph_phongban) {
                ph_phongban.value = d.don_vi_trong_id || '';
            }
            openVBD('popupPhatHanh');
        });
}

function xacNhanPhatHanh() {
    if (!_phatHanhId) return;
    
    let trichYeu = document.getElementById('ph_trichyeu').value.trim();
    let ngayBanHanh = document.getElementById('ph_ngay').value;
    let ph_phongban = document.getElementById('ph_phongban');
    
    if (!trichYeu) {
        App.showAlert('Vui lòng nhập trích yếu!');
        return;
    }
    
    if (ph_phongban && !ph_phongban.value) {
        App.showAlert('Vui lòng chọn phòng ban nhận để phân công!');
        return;
    }
    
    if (!ngayBanHanh) {
        App.showAlert('Vui lòng chọn ngày ban hành!');
        return;
    }
    
    let data = {
        trich_yeu: trichYeu,
        ngay_ban_hanh: ngayBanHanh,
        don_vi_trong_id: ph_phongban ? ph_phongban.value : null
    };
    apiPost('/api/van-ban-di/' + _phatHanhId + '/phat-hanh/', data, () => {
        App.showSuccess('Phát hành thành công', () => {
            window.location.reload();
        });
    });
}

// ---- LỊCH SỬ ----
function moLichSu(vanBanId) {
    fetch('/api/van-ban-di/' + vanBanId + '/lich-su/')
        .then(r => r.json())
        .then(res => {
            let tbody = document.querySelector('#historyOverlay .history-table-full tbody');
            if (!tbody) return;
            tbody.innerHTML = '';
            if (!res.data || !res.data.length) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color:#999;padding:20px;">Chưa có lịch sử chỉnh sửa</td></tr>';
            } else {
                res.data.forEach((ls, i) => {
                    let ttHtml = '';
                    if (ls.trang_thai_moi) {
                        ttHtml = ls.trang_thai_cu && ls.trang_thai_cu !== ls.trang_thai_moi
                            ? ` <span style="color:#888;font-size:12px;">(${ls.trang_thai_cu} → <strong>${ls.trang_thai_moi}</strong>)</span>`
                            : ` <span style="color:#888;font-size:12px;">(→ <strong>${ls.trang_thai_moi}</strong>)</span>`;
                    }
                    let noiDungHtml = ls.noi_dung.replace(/Cập nhật/g, '<strong>Cập nhật</strong>');
                    tbody.innerHTML += `<tr>
                    <td class="text-center">${i + 1}</td>
                    <td class="text-center">${ls.thoi_gian}</td>
                    <td>${ls.nguoi_thuc_hien}</td>
                    <td class="text-center">${ls.ma_van_ban}</td>
                    <td>${ls.trich_yeu}</td>
                    <td class="text-left">${noiDungHtml}${ttHtml}</td>
                </tr>`;
                });
            }
            closeVBD('modalDetail');
            openVBD('historyOverlay');
        })
        .catch(() => {
            let tbody = document.querySelector('#historyOverlay .history-table-full tbody');
            if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color:#e74c3c;padding:20px;">Không tải được lịch sử</td></tr>';
            openVBD('historyOverlay');
        });
}

// ---- TÌM ĐỂ XỬ LÝ ----
function timDeXuLy() {
    const soKyHieu = document.getElementById('ct_sokyhieu')?.value || '';
    const url = '/xu-ly-van-ban/' + (soKyHieu ? '?so_ky_hieu=' + encodeURIComponent(soKyHieu) : '');
    window.location.href = url;
}

// ---- RELOAD ĐƠN VỊ DYNAMIC ----
let _cachedDonVi = { trong: [], ngoai: [] };

function reloadDonViDropdowns() {
    fetch('/api/don-vi/list/')
        .then(r => r.json())
        .then(res => {
            if (res.status !== 'success') return;
            _cachedDonVi = res;
        });
}

// Gọi khi trang load
document.addEventListener('DOMContentLoaded', reloadDonViDropdowns);

function loadUsersByDept(deptId, targetSelectId, selectedValue = null) {
    const select = document.getElementById(targetSelectId);
    if (!select) return;
    select.innerHTML = '<option value="">--- Chọn người xử lý ---</option>';
    if (!deptId) return;

    fetch(`/api/nguoi-dung/list/?dept=${deptId}&page_size=all`)
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success' && res.data) {
                res.data.forEach(user => {
                    const opt = document.createElement('option');
                    opt.value = user.id;
                    opt.textContent = `${user.fullname} (${user.role_name})`;
                    if (selectedValue && String(user.id) === String(selectedValue)) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
            }
        });
}

document.addEventListener('DOMContentLoaded', () => {
    const donViBH = document.getElementById('donViBH');
    if (donViBH) {
        donViBH.addEventListener('input', function () {
            let val = this.value;
            let dept = _cachedDonVi.trong.find(i => i.ten === val);
            if (dept) loadUsersByDept(dept.id, 'nguoiSoanThao');
        });
    }

    const editDonViBH = document.getElementById('edit_donViBH');
    if (editDonViBH) {
        editDonViBH.addEventListener('input', function () {
            let val = this.value;
            let dept = _cachedDonVi.trong.find(i => i.ten === val);
            if (dept) loadUsersByDept(dept.id, 'edit_nguoisoan');
        });
    }
});
