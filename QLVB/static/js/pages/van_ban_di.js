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
            else App.showError(res.message);
        })
        .catch(() => App.showError('Có lỗi xảy ra, vui lòng thử lại.'));
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
            else App.showError(res.message);
        })
        .catch(() => App.showError('Có lỗi xảy ra, vui lòng thử lại.'));
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

            const loaiEl = document.getElementById('loaiVB');
            if (loaiEl) loaiEl.value = 'Công văn';

            // Lấy gợi ý số ký hiệu theo loại mặc định
            autoCapSoKyHieu('Công văn');
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

            // AUTO-08: Hiển thị tóm tắt AI cho Văn bản đi
            const ctAiContent = document.getElementById('ct_ai_summary_content');
            const btnCopyCt = document.getElementById('btnCopyAISummaryVBD');
            if (ctAiContent) {
                if (d.tom_tat_ai) {
                    ctAiContent.innerHTML = d.tom_tat_ai;
                    if (btnCopyCt) btnCopyCt.style.display = 'inline-block';
                } else {
                    ctAiContent.innerHTML = `
                        <div style="color: #64748b; font-style: italic;">
                            <i class="fas fa-info-circle text-primary me-1"></i> Chưa có bản tóm tắt AI. Nhấn <b>"Phân tích AI"</b> để hệ thống tự động đọc và tóm tắt văn bản này.
                        </div>
                    `;
                    if (btnCopyCt) btnCopyCt.style.display = 'none';
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
        App.showError('Vui lòng đính kèm tài liệu!');
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
        App.showError('Vui lòng đính kèm tài liệu!');
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

function autoCapSoKyHieu(loaiVb) {
    let url = '/api/van-ban-di/goi-y-so-ky-hieu/';
    if (loaiVb) url += '?loai_vb=' + encodeURIComponent(loaiVb);
    fetch(url)
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success' && res.suggested) {
                const el = document.getElementById('soKyHieu');
                if (el) el.value = res.suggested;
            }
        })
        .catch(err => console.error('Lỗi cấp số ký hiệu:', err));
}

function xacNhanPheDuyet(action) {
    if (!_pheDuyetId) return;

    if (action === true) action = 'dong_y';
    if (action === false) action = 'tu_choi';

    let ghiChuEl = document.getElementById('pd_ghichu');
    let ghiChu = ghiChuEl ? ghiChuEl.value.trim() : '';

    let chuKy = _sigCanvas ? _sigCanvas.toDataURL() : '';
    let isEmpty = true;
    if (_sigCanvas) {
        let blank = document.createElement('canvas');
        blank.width = _sigCanvas.width;
        blank.height = _sigCanvas.height;
        if (_sigCanvas.toDataURL() !== blank.toDataURL()) isEmpty = false;
    }

    if (action === 'dong_y') {
        if (isEmpty) {
            App.showAlert("Vui lòng ký tên vào ô chữ ký số trước khi phê duyệt.");
            return;
        }
    } else if (action === 'yeu_cau_chinh_sua') {
        if (!ghiChu) {
            App.showAlert("Vui lòng nhập nội dung/lý do yêu cầu chỉnh sửa vào ô Ghi chú.");
            if (ghiChuEl) ghiChuEl.focus();
            return;
        }
    } else if (action === 'tu_choi') {
        if (!ghiChu) {
            App.showAlert("Vui lòng nhập lý do từ chối vào ô Ghi chú.");
            if (ghiChuEl) ghiChuEl.focus();
            return;
        }
    }

    let data = {
        action: action,
        chap_nhan: (action === 'dong_y'),
        ghi_chu: ghiChu,
        chu_ky_so: (action === 'dong_y' && !isEmpty) ? chuKy : ''
    };
    
    fetch('/api/van-ban-di/' + _pheDuyetId + '/phe-duyet/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(res => {
        if (res.status === 'success') {
            closeVBD('popupPheDuyet');
            let successMsg = res.message || (action === 'dong_y' ? 'Phê duyệt văn bản thành công!' : 'Đã gửi phản hồi thành công!');
            App.showSuccess(successMsg, () => {
                window.location.reload();
            });
        } else {
            App.showError('Lỗi: ' + res.message);
        }
    })
    .catch(err => {
        console.error(err);
        App.showError('Có lỗi xảy ra, vui lòng thử lại.');
    });
}

// ---- PHÁT HÀNH ----
let _phatHanhId = null;

function togglePhatHanhScope(scope) {
    const grpInternal = document.getElementById('ph_group_internal');
    const grpExternal = document.getElementById('ph_group_external');
    
    if (scope === 'internal') {
        if (grpInternal) grpInternal.style.display = 'flex';
        if (grpExternal) grpExternal.style.display = 'none';
    } else if (scope === 'external') {
        if (grpInternal) grpInternal.style.display = 'none';
        if (grpExternal) grpExternal.style.display = 'block';
    } else if (scope === 'both') {
        if (grpInternal) grpInternal.style.display = 'flex';
        if (grpExternal) grpExternal.style.display = 'block';
    }
}

function updateExternalEmailInfo(select) {
    const opt = select.options[select.selectedIndex];
    const email = opt ? opt.getAttribute('data-email') : '';
    const emailBox = document.getElementById('ph_email_info_box');
    const missingBox = document.getElementById('ph_email_missing_box');
    const emailDisplay = document.getElementById('ph_email_display');

    if (!select.value) {
        if (emailBox) emailBox.style.display = 'none';
        if (missingBox) missingBox.style.display = 'none';
        return;
    }

    if (email) {
        if (emailDisplay) emailDisplay.textContent = email;
        if (emailBox) emailBox.style.display = 'block';
        if (missingBox) missingBox.style.display = 'none';
    } else {
        if (emailBox) emailBox.style.display = 'none';
        if (missingBox) missingBox.style.display = 'block';
    }
}

function phatHanhVanBan(btnOrId) {
    let id;
    if (typeof btnOrId === 'object' && btnOrId !== null) {
        id = btnOrId.closest("tr").dataset.id;
    } else {
        id = btnOrId;
    }
    _phatHanhId = id;

    // Reset scope về mặc định
    const radios = document.querySelectorAll('input[name="ph_scope"]');
    if (radios.length > 0) {
        radios[0].checked = true;
        togglePhatHanhScope('internal');
    }
    const ph_donvi_ngoai = document.getElementById("ph_donvi_ngoai");
    if (ph_donvi_ngoai) {
        ph_donvi_ngoai.value = '';
        updateExternalEmailInfo(ph_donvi_ngoai);
    }

    const ph_trichyeu = document.getElementById("ph_trichyeu");
    if (ph_trichyeu) ph_trichyeu.value = 'Đang tải thông tin...';

    const ph_ngay = document.getElementById("ph_ngay");
    if (ph_ngay) ph_ngay.value = new Date().toISOString().split('T')[0];

    const ph_phongban = document.getElementById("ph_phongban");
    if (ph_phongban) ph_phongban.value = '';

    openVBD('popupPhatHanh');

    fetch('/api/van-ban-di/' + _phatHanhId + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success' && res.data) {
                let d = res.data;
                if (ph_trichyeu) ph_trichyeu.value = d.trich_yeu || '';
                if (d.ngay_ban_hanh && ph_ngay) {
                    let parts = d.ngay_ban_hanh.split("/");
                    if (parts.length === 3) {
                        ph_ngay.value = parts[2] + "-" + parts[1] + "-" + parts[0];
                    }
                }
                if (ph_phongban && d.don_vi_trong_id) {
                    ph_phongban.value = d.don_vi_trong_id;
                }

                if (d.don_vi_ngoai_id && ph_donvi_ngoai) {
                    ph_donvi_ngoai.value = d.don_vi_ngoai_id;
                    if (d.don_vi_trong_id) {
                        const rBoth = document.querySelector('input[name="ph_scope"][value="both"]');
                        if (rBoth) { rBoth.checked = true; togglePhatHanhScope('both'); }
                    } else {
                        const rExt = document.querySelector('input[name="ph_scope"][value="external"]');
                        if (rExt) { rExt.checked = true; togglePhatHanhScope('external'); }
                    }
                    updateExternalEmailInfo(ph_donvi_ngoai);
                }
            }
        })
        .catch(err => {
            console.error('Lỗi khi tải chi tiết văn bản phát hành:', err);
            if (ph_trichyeu) ph_trichyeu.value = '';
        });
}

function xacNhanPhatHanh() {
    if (!_phatHanhId) return;
    
    let trichYeu = document.getElementById('ph_trichyeu').value.trim();
    let ngayBanHanh = document.getElementById('ph_ngay').value;
    let scopeRadio = document.querySelector('input[name="ph_scope"]:checked');
    let scope = scopeRadio ? scopeRadio.value : 'internal';
    let ph_phongban = document.getElementById('ph_phongban');
    let ph_donvi_ngoai = document.getElementById('ph_donvi_ngoai');
    let submitBtn = document.getElementById('btnSubmitPhatHanh');
    
    if (!trichYeu) {
        App.showAlert('Vui lòng nhập trích yếu!');
        return;
    }

    if (scope === 'internal' || scope === 'both') {
        if (ph_phongban && !ph_phongban.value) {
            App.showAlert('Vui lòng chọn phòng ban nội bộ nhận văn bản!');
            return;
        }
    }

    if (scope === 'external' || scope === 'both') {
        if (ph_donvi_ngoai && !ph_donvi_ngoai.value) {
            App.showAlert('Vui lòng chọn đơn vị bên ngoài nhận phát hành!');
            return;
        }
        const opt = ph_donvi_ngoai.options[ph_donvi_ngoai.selectedIndex];
        const email = opt ? opt.getAttribute('data-email') : '';
        if (!email) {
            App.showAlert('Đơn vị bên ngoài được chọn chưa có email cấu hình trong hệ thống! Vui lòng cập nhật email tại Quản lý đơn vị ngoài.');
            return;
        }
    }

    if (!ngayBanHanh) {
        App.showAlert('Vui lòng chọn ngày ban hành!');
        return;
    }

    let data = {
        trich_yeu: trichYeu,
        ngay_ban_hanh: ngayBanHanh,
        ph_scope: scope,
        don_vi_trong_id: (scope === 'internal' || scope === 'both') ? (ph_phongban ? ph_phongban.value : null) : null,
        don_vi_ngoai_id: (scope === 'external' || scope === 'both') ? (ph_donvi_ngoai ? ph_donvi_ngoai.value : null) : null
    };

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang phát hành...';
    }

    fetch('/api/van-ban-di/' + _phatHanhId + '/phat-hanh/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(data)
    })
    .then(r => r.json())
    .then(res => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Phát hành';
        }
        if (res.status === 'success') {
            closeVBD('popupPhatHanh');
            let successMsg = res.message || 'Phát hành thành công!';
            App.showSuccess(successMsg, () => {
                window.location.reload();
            });
        } else {
            App.showError('Lỗi: ' + res.message);
        }
    })
    .catch(err => {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Phát hành';
        }
        console.error(err);
        App.showError('Có lỗi xảy ra khi phát hành văn bản!');
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


// ==============================================================================
// AUTO-03: TỰ ĐỘNG SINH VĂN BẢN TỪ BIỂU MẪU CHUẨN DOCX (NGHỊ ĐỊNH 30/2020)
// ==============================================================================

function taiBieuMauWord(mode) {
    let loaiVb = '', soKyHieu = '', trichYeu = '', donVi = '', ngayBanHanh = '';
    if (mode === 'edit') {
        loaiVb = document.getElementById('edit_loai_vb') ? document.getElementById('edit_loai_vb').value : '';
        soKyHieu = document.getElementById('edit_so_ky_hieu') ? document.getElementById('edit_so_ky_hieu').value : '';
        trichYeu = document.getElementById('edit_trich_yeu') ? document.getElementById('edit_trich_yeu').value : '';
        donVi = (document.getElementById('edit_don_vi_ngoai') ? document.getElementById('edit_don_vi_ngoai').value : '') || 
                (document.getElementById('edit_don_vi_nhan') ? document.getElementById('edit_don_vi_nhan').value : '');
        ngayBanHanh = document.getElementById('edit_ngay_ban_hanh') ? document.getElementById('edit_ngay_ban_hanh').value : '';
    } else {
        loaiVb = document.getElementById('loaiVB') ? document.getElementById('loaiVB').value : '';
        soKyHieu = document.getElementById('soKyHieu') ? document.getElementById('soKyHieu').value : '';
        trichYeu = document.getElementById('trichYeu') ? document.getElementById('trichYeu').value : '';
        donVi = (document.getElementById('donViNgoai') ? document.getElementById('donViNgoai').value : '') || 
                (document.getElementById('donViTrong') ? document.getElementById('donViTrong').value : '');
        ngayBanHanh = document.getElementById('ngayBanHanh') ? document.getElementById('ngayBanHanh').value : '';
    }

    if (!loaiVb) loaiVb = 'Công văn';
    let url = `/api/van-ban-di/tao-bieu-mau/?loai_vb=${encodeURIComponent(loaiVb)}&so_ky_hieu=${encodeURIComponent(soKyHieu)}&trich_yeu=${encodeURIComponent(trichYeu)}&don_vi=${encodeURIComponent(donVi)}&ngay_ban_hanh=${encodeURIComponent(ngayBanHanh)}`;
    window.open(url, '_blank');
}

async function tuDongTaoVaDinhKemDocx(mode) {
    let loaiVb = '', soKyHieu = '', trichYeu = '', donVi = '', ngayBanHanh = '';
    let fileInput = null;
    let labelElem = null;

    if (mode === 'edit') {
        loaiVb = document.getElementById('edit_loai_vb') ? document.getElementById('edit_loai_vb').value : '';
        soKyHieu = document.getElementById('edit_so_ky_hieu') ? document.getElementById('edit_so_ky_hieu').value : '';
        trichYeu = document.getElementById('edit_trich_yeu') ? document.getElementById('edit_trich_yeu').value : '';
        donVi = (document.getElementById('edit_don_vi_ngoai') ? document.getElementById('edit_don_vi_ngoai').value : '') || 
                (document.getElementById('edit_don_vi_nhan') ? document.getElementById('edit_don_vi_nhan').value : '');
        ngayBanHanh = document.getElementById('edit_ngay_ban_hanh') ? document.getElementById('edit_ngay_ban_hanh').value : '';
        fileInput = document.getElementById('edit_file_input');
    } else {
        loaiVb = document.getElementById('loaiVB') ? document.getElementById('loaiVB').value : '';
        soKyHieu = document.getElementById('soKyHieu') ? document.getElementById('soKyHieu').value : '';
        trichYeu = document.getElementById('trichYeu') ? document.getElementById('trichYeu').value : '';
        donVi = (document.getElementById('donViNgoai') ? document.getElementById('donViNgoai').value : '') || 
                (document.getElementById('donViTrong') ? document.getElementById('donViTrong').value : '');
        ngayBanHanh = document.getElementById('ngayBanHanh') ? document.getElementById('ngayBanHanh').value : '';
        fileInput = document.getElementById('fileInput');
        labelElem = document.getElementById('fileLabel');
    }

    if (!loaiVb) {
        loaiVb = 'Công văn';
        if (document.getElementById('loaiVB')) document.getElementById('loaiVB').value = 'Công văn';
    }

    if (!soKyHieu) {
        if (typeof autoCapSoKyHieu === 'function') {
            autoCapSoKyHieu(loaiVb);
            soKyHieu = document.getElementById('soKyHieu') ? document.getElementById('soKyHieu').value : '';
        }
    }

    let evtTarget = (typeof event !== 'undefined' && event) ? event.currentTarget : null;
    let originalHtml = evtTarget ? evtTarget.innerHTML : '';
    if (evtTarget) {
        evtTarget.disabled = true;
        evtTarget.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang sinh...';
    }

    try {
        let url = `/api/van-ban-di/tao-bieu-mau/?loai_vb=${encodeURIComponent(loaiVb)}&so_ky_hieu=${encodeURIComponent(soKyHieu)}&trich_yeu=${encodeURIComponent(trichYeu)}&don_vi=${encodeURIComponent(donVi)}&ngay_ban_hanh=${encodeURIComponent(ngayBanHanh)}`;
        let res = await fetch(url);
        if (!res.ok) throw new Error("Không thể sinh biểu mẫu");
        let blob = await res.blob();

        let safeSo = (soKyHieu || 'MauVanBan').replace(/[^a-zA-Z0-9_\-]/g, '_');
        let safeLoai = loaiVb.replace(/[^a-zA-Z0-9_\-]/g, '_');
        let fileName = `${safeSo}_${safeLoai}.docx`;

        let file = new File([blob], fileName, { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' });

        if (window.DataTransfer) {
            const dt = new DataTransfer();
            dt.items.add(file);
            if (fileInput) {
                fileInput.files = dt.files;
            }
        }

        if (mode === 'edit') {
            if (typeof previewEditFile === 'function') {
                previewEditFile(fileInput);
            }
        } else {
            if (labelElem) {
                labelElem.innerHTML = `<span style="color: #10b981; font-weight: 600;"><i class="fas fa-check-circle"></i> Đã tự sinh & đính kèm: <b>${fileName}</b> (${(file.size / 1024).toFixed(1)} KB)</span>`;
            }
        }

        if (window.App && App.showSuccess) {
            App.showSuccess(`Đã sinh biểu mẫu chuẩn và tự động đính kèm vào hồ sơ!`);
        } else {
            alert(`Đã sinh biểu mẫu chuẩn (${fileName}) và tự động đính kèm thành công!`);
        }
    } catch (err) {
        console.error(err);
        if (window.App && App.showError) {
            App.showError("Lỗi khi sinh biểu mẫu: " + err.message);
        } else {
            alert("Lỗi khi sinh biểu mẫu: " + err.message);
        }
    } finally {
        if (evtTarget) {
            evtTarget.disabled = false;
            evtTarget.innerHTML = originalHtml;
        }
    }
}


// ==============================================================================
// AUTO-06: XỬ LÝ NGOẠI LỆ HỆ THỐNG & HÀNG ĐỢI THỬ LẠI (RETRY QUEUE)
// ==============================================================================

function openModalNgoaiLe() {
    let el = document.getElementById('modalNgoaiLe');
    if (el) el.style.display = 'flex';
    loadDanhSachNgoaiLe();
}

function closeModalNgoaiLe() {
    let el = document.getElementById('modalNgoaiLe');
    if (el) el.style.display = 'none';
}

function capNhatBadgeNgoaiLe() {
    fetch('/api/ngoai-le/danh-sach/')
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success') {
                let count = res.pending_count || 0;
                let badges = document.querySelectorAll('#badgeNgoaiLeCount');
                badges.forEach(b => {
                    if (count > 0) {
                        b.textContent = count;
                        b.style.display = 'inline-block';
                    } else {
                        b.style.display = 'none';
                    }
                });
            }
        })
        .catch(() => {});
}

function loadDanhSachNgoaiLe() {
    let tbody = document.getElementById('tblNgoaiLeBody');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 25px; color: #94a3b8;"><i class="fas fa-spinner fa-spin"></i> Đang tải danh sách hàng đợi...</td></tr>';

    fetch('/api/ngoai-le/danh-sach/')
        .then(r => r.json())
        .then(res => {
            if (res.status !== 'success') {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">Lỗi: ${res.message || 'Không thể tải danh sách'}</td></tr>`;
                return;
            }

            let count = res.pending_count || 0;
            let badges = document.querySelectorAll('#badgeNgoaiLeCount');
            badges.forEach(b => {
                if (count > 0) {
                    b.textContent = count;
                    b.style.display = 'inline-block';
                } else {
                    b.style.display = 'none';
                }
            });

            if (!res.items || res.items.length === 0) {
                tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 30px; color: #10b981;"><i class="fas fa-check-circle" style="font-size: 24px; display: block; margin-bottom: 8px;"></i> Không có tác vụ ngoại lệ nào. Toàn bộ hệ thống đang hoạt động an toàn!</td></tr>`;
                return;
            }

            let html = '';
            res.items.forEach(it => {
                let statusBadge = '';
                if (it.trang_thai === 'CHO_XU_LY') {
                    statusBadge = '<span class="badge" style="background: #f59e0b; color: #fff; padding: 4px 8px; border-radius: 4px;">Chờ thử lại</span>';
                } else if (it.trang_thai === 'DANG_THU_LAI') {
                    statusBadge = '<span class="badge" style="background: #3b82f6; color: #fff; padding: 4px 8px; border-radius: 4px;"><i class="fas fa-spinner fa-spin"></i> Đang thử</span>';
                } else if (it.trang_thai === 'THANH_CONG') {
                    statusBadge = '<span class="badge" style="background: #10b981; color: #fff; padding: 4px 8px; border-radius: 4px;"><i class="fas fa-check"></i> Thành công</span>';
                } else if (it.trang_thai === 'THAT_BAI') {
                    statusBadge = '<span class="badge" style="background: #ef4444; color: #fff; padding: 4px 8px; border-radius: 4px;"><i class="fas fa-exclamation-triangle"></i> Thất bại</span>';
                } else {
                    statusBadge = `<span class="badge" style="background: #94a3b8; color: #fff; padding: 4px 8px; border-radius: 4px;">${it.trang_thai_display}</span>`;
                }

                let actions = '';
                if (it.trang_thai === 'CHO_XU_LY' || it.trang_thai === 'THAT_BAI') {
                    actions = `
                        <button type="button" class="btn btn-sm btn-primary" onclick="thuLaiNgoaiLe(${it.id})" title="Thử lại ngay" style="padding: 3px 8px; font-size: 12px; margin-right: 4px;">
                            <i class="fas fa-redo"></i> Thử lại
                        </button>
                        <button type="button" class="btn btn-sm btn-secondary" onclick="huyNgoaiLe(${it.id})" title="Hủy bỏ" style="padding: 3px 8px; font-size: 12px;">
                            <i class="fas fa-times"></i>
                        </button>
                    `;
                } else {
                    actions = `<span style="color: #94a3b8; font-size: 12px;">Đã hoàn tất</span>`;
                }

                html += `
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 10px; text-align: center; font-weight: bold; color: #64748b;">#${it.id}</td>
                        <td style="padding: 10px; font-weight: 500;">
                            <i class="fas fa-envelope-open-text text-primary me-1"></i> ${it.loai_display}
                        </td>
                        <td style="padding: 10px;">
                            <div style="font-weight: 600; color: #1e293b;">${it.so_ky_hieu ? `<span style="color: #0284c7;">[${it.so_ky_hieu}]</span> ` : ''}${it.tieu_de}</div>
                            <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;">Tạo lúc: ${it.ngay_tao}</div>
                        </td>
                        <td style="padding: 10px; color: #b91c1c; font-size: 12px; max-width: 250px; word-break: break-word;">
                            ${it.mo_ta_loi || 'Không có mô tả chi tiết'}
                            ${it.ghi_chu ? `<div style="color: #10b981; font-size: 11px; margin-top: 3px;"><i class="fas fa-check"></i> ${it.ghi_chu}</div>` : ''}
                        </td>
                        <td style="padding: 10px; text-align: center; font-weight: bold;">
                            ${it.so_lan_thu_lai}/${it.so_lan_toi_da}
                        </td>
                        <td style="padding: 10px; text-align: center;">${statusBadge}</td>
                        <td style="padding: 10px; text-align: center;">${actions}</td>
                    </tr>
                `;
            });
            tbody.innerHTML = html;
        })
        .catch(err => {
            console.error(err);
            tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 20px; color: #dc3545;">Lỗi kết nối máy chủ khi tải hàng đợi.</td></tr>`;
        });
}

function thuLaiNgoaiLe(id) {
    if (!confirm(`Bạn có chắc chắn muốn thực thi thử lại tác vụ ngoại lệ #${id}?`)) return;

    fetch(`/api/ngoai-le/${id}/thu-lai/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(r => r.json())
    .then(res => {
        if (res.status === 'success') {
            if (window.App && App.showSuccess) App.showSuccess(res.message);
            else alert(res.message);
        } else {
            if (window.App && App.showError) App.showError(res.message);
            else alert("Lỗi: " + res.message);
        }
        loadDanhSachNgoaiLe();
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối mạng khi kích hoạt thử lại!");
    });
}

function thuLaiTatCaNgoaiLe() {
    if (!confirm("Bạn có chắc muốn kích hoạt thử lại TẤT CẢ các tác vụ đang chờ trong hàng đợi?")) return;

    fetch('/api/ngoai-le/thu-lai-tat-ca/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(r => r.json())
    .then(res => {
        if (res.status === 'success') {
            if (window.App && App.showSuccess) App.showSuccess(res.message);
            else alert(res.message);
        } else {
            if (window.App && App.showError) App.showError(res.message);
            else alert("Lỗi: " + res.message);
        }
        loadDanhSachNgoaiLe();
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối khi thử lại tất cả!");
    });
}

function huyNgoaiLe(id) {
    if (!confirm(`Bạn có chắc chắn muốn hủy bỏ tác vụ ngoại lệ #${id}?`)) return;

    fetch(`/api/ngoai-le/${id}/huy/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(r => r.json())
    .then(res => {
        loadDanhSachNgoaiLe();
    })
    .catch(err => {
        console.error(err);
        alert("Lỗi kết nối khi hủy tác vụ!");
    });
}

// Tự động kiểm tra số lượng tác vụ trong hàng đợi khi tải trang
document.addEventListener('DOMContentLoaded', () => {
    capNhatBadgeNgoaiLe();
});


// ==============================================================================
// GIAI ĐOẠN 3 (PHASE 3): AI SMART SUMMARY (VAN BAN DI)
// ==============================================================================

function yeuCauTomTatAIVanBanDi() {
    if (!_detailId) {
        alert("Không tìm thấy mã văn bản đi!");
        return;
    }
    const contentDiv = document.getElementById('ct_ai_summary_content');
    const btn = document.getElementById('btnRunAISummaryVBD');
    const btnText = document.getElementById('btnRunAISummaryVBDText');
    const btnCopy = document.getElementById('btnCopyAISummaryVBD');

    if (btn) btn.disabled = true;
    if (btnText) btnText.textContent = 'Đang phân tích...';
    if (contentDiv) {
        contentDiv.innerHTML = `
            <div style="padding: 15px; text-align: center; color: #6366f1;">
                <i class="fas fa-spinner fa-spin" style="font-size: 20px; display: block; margin-bottom: 6px;"></i>
                AI đang đọc hiểu nội dung tệp đính kèm và tổng hợp 3-5 ý chính...
            </div>
        `;
    }

    fetch('/api/ai/' + _detailId + '/summarize/?type=di&refresh=1', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(r => r.json())
    .then(res => {
        if (res.status === 'success') {
            if (contentDiv) contentDiv.innerHTML = res.summary_html;
            if (btnCopy) {
                btnCopy.style.display = 'inline-block';
                btnCopy.dataset.plain = res.plain_text || '';
            }
        } else {
            if (contentDiv) {
                contentDiv.innerHTML = `<div style="color: #ef4444;"><i class="fas fa-exclamation-triangle me-1"></i> Lỗi phân tích: ${res.message}</div>`;
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (contentDiv) {
            contentDiv.innerHTML = '<div style="color: #ef4444;"><i class="fas fa-exclamation-triangle me-1"></i> Lỗi kết nối máy chủ khi tóm tắt AI.</div>';
        }
    })
    .finally(() => {
        if (btn) btn.disabled = false;
        if (btnText) btnText.textContent = 'Phân tích lại';
    });
}

function saoChepTomTatAIVanBanDi() {
    const btnCopy = document.getElementById('btnCopyAISummaryVBD');
    const plain = btnCopy ? btnCopy.dataset.plain : '';
    if (plain && navigator.clipboard) {
        navigator.clipboard.writeText(plain).then(() => {
            if (window.App && App.showSuccess) App.showSuccess("Đã sao chép bản tóm tắt AI vào clipboard!");
            else alert("Đã sao chép bản tóm tắt vào clipboard!");
        });
    } else {
        alert("Không có nội dung để sao chép!");
    }
}


// ==============================================================================
// GIAI ĐOẠN 3 (PHASE 3): AI OCR & TỰ ĐỘNG ĐIỀN THÔNG TIN VĂN BẢN ĐI
// ==============================================================================

function _highlightOCRFieldVBD(input) {
    if (!input) return;
    input.style.transition = 'all 0.3s ease';
    input.style.borderColor = '#10b981';
    input.style.boxShadow = '0 0 0 3px rgba(16, 185, 129, 0.25)';
    input.style.backgroundColor = '#f0fdf4';
    setTimeout(() => {
        input.style.borderColor = '';
        input.style.boxShadow = '';
        input.style.backgroundColor = '';
    }, 3500);
}

function xuLyTepDinhKemVanBanDi(inputOrFile) {
    let file = null;
    if (inputOrFile instanceof File) {
        file = inputOrFile;
    } else if (inputOrFile && inputOrFile.files && inputOrFile.files[0]) {
        file = inputOrFile.files[0];
    }

    const labelElem = document.getElementById('fileLabel');
    if (file) {
        if (labelElem) {
            labelElem.innerHTML = `
                <div style="font-weight: 600; color: #0284c7;">
                    <i class="fas fa-file-alt me-1"></i> ${file.name}
                    <span style="font-size: 12px; color: #64748b; font-weight: normal;">(${(file.size / 1024).toFixed(1)} KB)</span>
                </div>
            `;
        }
        // TỰ ĐỘNG QUÉT OCR & ĐIỀN DỮ LIỆU TỨC THÌ
        quyetDuLieuOCRVanBanDi(file);
    } else {
        if (labelElem) {
            labelElem.innerHTML = 'Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính';
        }
        const badge = document.getElementById('vbd_ocr_status_badge');
        if (badge) badge.style.display = 'none';
    }
}

function quyetDuLieuOCRVanBanDi(customFile) {
    let file = customFile;
    if (!file) {
        const fi = document.getElementById('fileInput');
        if (fi && fi.files && fi.files[0]) {
            file = fi.files[0];
        }
    }

    if (!file) {
        alert("Vui lòng chọn hoặc kéo thả tệp văn bản trước khi quét OCR!");
        const fi = document.getElementById('fileInput');
        if (fi) fi.click();
        return;
    }

    const btn = document.getElementById('btnOcrScanVBD');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang quét OCR...';
    }

    const badge = document.getElementById('vbd_ocr_status_badge');
    const badgeText = document.getElementById('vbd_ocr_status_text');
    if (badge) {
        badge.style.display = 'block';
        badge.style.background = '#eff6ff';
        badge.style.borderColor = '#93c5fd';
        badge.style.color = '#1e40af';
        if (badgeText) badgeText.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> <b>AI OCR đang quét tệp:</b> Đang trích xuất Số ký hiệu, Loại văn bản, Ngày tháng, Cơ quan ban hành...';
    }

    const fd = new FormData();
    fd.append('tep_dinh_kem', file);

    fetch('/api/ai/ocr-extract/', {
        method: 'POST',
        headers: { 'X-CSRFToken': getCookie('csrftoken') },
        body: fd
    })
    .then(r => r.json())
    .then(res => {
        if (res.status === 'success') {
            const d = res.data;

            // 1. Trích yếu
            const trichYeuEl = document.getElementById('trichYeu');
            if (trichYeuEl && d.trich_yeu) {
                trichYeuEl.value = d.trich_yeu;
                _highlightOCRFieldVBD(trichYeuEl);
            }

            // 2. Loại văn bản
            const loaiVbEl = document.getElementById('loaiVB');
            if (loaiVbEl && d.loai_van_ban) {
                for (let i = 0; i < loaiVbEl.options.length; i++) {
                    if (loaiVbEl.options[i].value.toLowerCase() === d.loai_van_ban.toLowerCase()) {
                        loaiVbEl.selectedIndex = i;
                        break;
                    }
                }
                _highlightOCRFieldVBD(loaiVbEl);
            }

            // 3. Số ký hiệu
            const soKyHieuEl = document.getElementById('soKyHieu');
            if (soKyHieuEl && d.so_ky_hieu) {
                soKyHieuEl.value = d.so_ky_hieu;
                _highlightOCRFieldVBD(soKyHieuEl);
            }

            // 4. Ngày ban hành
            const ngayEl = document.getElementById('ngayBanHanh');
            if (ngayEl && d.ngay_ban_hanh) {
                ngayEl.value = d.ngay_ban_hanh;
                _highlightOCRFieldVBD(ngayEl);
            }

            // 5. Đơn vị bên ngoài
            const dvNgoaiEl = document.getElementById('donViNgoai');
            if (dvNgoaiEl && (d.co_quan_ban_hanh || d.don_vi_ngoai_ten)) {
                dvNgoaiEl.value = d.don_vi_ngoai_ten || d.co_quan_ban_hanh;
                _highlightOCRFieldVBD(dvNgoaiEl);
            }

            if (badge) {
                badge.style.background = '#f0fdf4';
                badge.style.borderColor = '#86efac';
                badge.style.color = '#166534';
                if (badgeText) {
                    badgeText.innerHTML = `✨ <b>AI OCR thành công:</b> Đã tự động điền các trường văn bản (Loại: <b>${d.loai_van_ban}</b> | Số: <b>${d.so_ky_hieu || 'Cấp tự động'}</b> | Ngày: <b>${d.ngay_ban_hanh}</b>)!`;
                }
            }
            if (window.App && App.showSuccess) {
                App.showSuccess("AI đã quét OCR và tự động điền các ô dữ liệu thành công!");
            }
        } else {
            if (badge) {
                badge.style.background = '#fef2f2';
                badge.style.borderColor = '#fca5a5';
                badge.style.color = '#991b1b';
                if (badgeText) badgeText.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> ${res.message || 'Không thể quét OCR nội dung văn bản này'}`;
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (badge) {
            badge.style.background = '#fef2f2';
            badge.style.borderColor = '#fca5a5';
            badge.style.color = '#991b1b';
            if (badgeText) badgeText.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Lỗi kết nối khi quét OCR!';
        }
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    });
}

// Khởi tạo kéo & thả cho modalForm Văn bản đi
document.addEventListener('DOMContentLoaded', () => {
    const uploadAreaVBD = document.getElementById('vbd_modal_upload_area');
    const fileInputVBD = document.getElementById('fileInput');

    if (uploadAreaVBD) {
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadAreaVBD.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadAreaVBD.style.borderColor = '#0284c7';
                uploadAreaVBD.style.backgroundColor = '#f0f9ff';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadAreaVBD.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadAreaVBD.style.borderColor = '';
                uploadAreaVBD.style.backgroundColor = '';
            }, false);
        });

        uploadAreaVBD.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                const file = dt.files[0];
                if (fileInputVBD) {
                    try { fileInputVBD.files = dt.files; } catch (err) {}
                }
                xuLyTepDinhKemVanBanDi(file);
            }
        }, false);
    }
});
