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

function goPage(page) {
    let url = new URL(window.location.href);
    url.searchParams.set('page', page);
    window.location.href = url.toString();
}

function openVBD(id) {
    let el = document.getElementById(id);
    if (el) {
        if (el.parentElement !== document.body) document.body.appendChild(el);
        if (el.classList.contains('vbd-popup-overlay')) {
            el.style.display = 'flex';
        } else {
            let overlay = document.getElementById('modalOverlay');
            if (overlay) overlay.style.display = 'block';
            el.style.display = 'flex';
        }
    }
}

function closeVBD(id) {
    let el = document.getElementById(id);
    if (el) {
        el.style.display = 'none';
        if (!el.classList.contains('vbd-popup-overlay')) {
            let overlay = document.getElementById('modalOverlay');
            if (overlay) overlay.style.display = 'none';
        }
    }
}

window.onclick = function(event) {
    if (event.target.classList.contains('vbd-popup-overlay')) {
        event.target.style.display = "none";
    }
}

function checkDonVi() {
    let ngoai = document.getElementById("donViNgoai");
    let bh = document.getElementById("donViBH");
    bh.disabled = (ngoai.value !== "");
    ngoai.disabled = (bh.value !== "");
}

function _renderFile(section, noFileEl, tepDinhKem) {
    if (tepDinhKem) {
        let fileName = tepDinhKem.split('/').pop();
        let ext = fileName.split('.').pop().toUpperCase();
        section.style.display = 'block';
        noFileEl.style.display = 'none';
        section.innerHTML = `<div class="vbd-file-item">
            <div class="vbd-file-info">
                <div class="vbd-file-icon">${ext}</div>
                <div class="vbd-file-details">
                    <a class="vbd-file-name" href="/media/${tepDinhKem}" target="_blank">${fileName}</a>
                    <span class="vbd-file-size"></span>
                </div>
            </div>
            <button type="button" style="background:none;border:none;cursor:pointer;color:#888;font-size:16px;padding:4px 8px;" onclick="xoaFileHienCo()">
                <i class="fas fa-trash"></i>
            </button>
        </div>`;
    } else {
        section.style.display = 'none';
        noFileEl.style.display = 'block';
        section.innerHTML = '';
    }
}

function xoaFileHienCo() {
    let section = document.getElementById('edit_file_section');
    let noFile  = document.getElementById('edit_no_file');
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
        document.getElementById("ct_donvi").value = [d.don_vi_ngoai ? d.don_vi_ngoai+' (BN)' : '', d.don_vi_trong ? d.don_vi_trong+' (BT)' : ''].filter(Boolean).join(', ');
        document.getElementById("ct_loaivb").value = d.loai_vb;
        document.getElementById("ct_nguoisoan").value = d.nguoi_soan;
        document.getElementById("ct_ngay").value = d.ngay_ban_hanh;
        document.getElementById("ct_trangthai").value = d.trang_thai;
        _renderFile(document.getElementById('ct_file_section'), document.getElementById('ct_no_file'), d.tep_dinh_kem);
        openVBD('modalDetail');
    });
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

// ---- THÊM MỚI ----
function _getFormData(trangThai) {
    let fd = new FormData();
    fd.append('so_ky_hieu', document.getElementById('soKyHieu').value);
    fd.append('trich_yeu', document.getElementById('trichYeu').value);
    fd.append('loai_vb', document.getElementById('loaiVB').value);
    fd.append('ngay_ban_hanh', document.getElementById('ngayBanHanh').value || '');
    fd.append('don_vi_ngoai_id', document.getElementById('donViNgoai').value || '');
    fd.append('don_vi_trong_id', document.getElementById('donViBH').value || '');
    fd.append('trang_thai', trangThai);
    let fileInput = document.getElementById('fileInput');
    if (fileInput && fileInput.files[0]) fd.append('tep_dinh_kem', fileInput.files[0]);
    return fd;
}

function luuDuThao() {
    apiPostForm('/api/van-ban-di/them-moi/', _getFormData('DU_THAO'), () => {
        closeVBD('modalForm');
        window.location.reload();
    });
}

function guiPheDuyet() {
    apiPostForm('/api/van-ban-di/them-moi/', _getFormData('CHO_PHE_DUYET'), () => {
        closeVBD('modalForm');
        window.location.reload();
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
                <span class="vbd-file-size">${(file.size/1024/1024).toFixed(2)} MB</span>
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

        // Set dropdown đơn vị — tìm theo text
        let selDonViNgoai = document.getElementById("edit_donvi");
        for (let o of selDonViNgoai.options) {
            if (o.text.includes(d.don_vi_ngoai) && o.value.startsWith('ngoai_')) { selDonViNgoai.value = o.value; break; }
        }

        // Map tên hiển thị -> mã
        let ttMap = {'Dự thảo':'DU_THAO','Chờ phê duyệt':'CHO_PHE_DUYET','Đã phê duyệt':'DA_PHE_DUYET','Đã phát hành':'DA_PHAT_HANH'};
        document.getElementById("edit_trangthai").value = ttMap[d.trang_thai] || 'DU_THAO';

        let parts = d.ngay_ban_hanh.split("/");
        if (parts.length === 3) document.getElementById("edit_ngay").value = parts[2]+"-"+parts[1]+"-"+parts[0];

        _renderFile(document.getElementById('edit_file_section'), document.getElementById('edit_no_file'), d.tep_dinh_kem);
        document.getElementById('edit_xoa_file').value = '0'; // reset flag
        openVBD('modalEdit');
    });
}

function luuCapNhat() {
    if (!_editId) return;
    let fd = new FormData();
    fd.append('so_ky_hieu', document.getElementById('edit_sokyhieu').value);
    fd.append('trich_yeu', document.getElementById('edit_trichyeu').value);
    fd.append('loai_vb', document.getElementById('edit_loaivb').value);
    fd.append('ngay_ban_hanh', document.getElementById('edit_ngay').value || '');
    fd.append('don_vi_ngoai_id', (document.getElementById('edit_donvi').value || '').replace('ngoai_',''));
    fd.append('trang_thai', document.getElementById('edit_trangthai').value);
    fd.append('xoa_file', document.getElementById('edit_xoa_file').value);
    let fileInput = document.getElementById('edit_file_input');
    if (fileInput && fileInput.files[0]) fd.append('tep_dinh_kem', fileInput.files[0]);
    apiPostForm('/api/van-ban-di/' + _editId + '/cap-nhat/', fd, () => {
        closeVBD('modalEdit');
        window.location.reload();
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
    _xoaId = btn.closest("tr").dataset.id;
    openVBD('popupRemoveFile');
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
}

function xacNhanPheDuyet(chap_nhan) {
    if (!_pheDuyetId) return;
    let data = {
        chap_nhan: chap_nhan,
        ghi_chu: document.getElementById('pd_ghichu') ? document.getElementById('pd_ghichu').value : '',
    };
    apiPost('/api/van-ban-di/' + _pheDuyetId + '/phe-duyet/', data, () => {
        closeVBD('popupPheDuyet');
        window.location.reload();
    });
}

// ---- PHÁT HÀNH ----
let _phatHanhId = null;

function phatHanhVanBan(btn) {
    let row = btn.closest("tr");
    _phatHanhId = row.dataset.id;
    let cells = row.getElementsByTagName("td");

    document.getElementById("ph_trichyeu").value = cells[2].innerText;
    let ngayRaw = cells[6].innerText.trim();
    let parts = ngayRaw.split("/");
    if (parts.length === 3) {
        document.getElementById("ph_ngay").value = parts[2] + "-" + parts[1] + "-" + parts[0];
    }
    openVBD('popupPhatHanh');
}

function xacNhanPhatHanh() {
    if (!_phatHanhId) return;
    let data = {
        trich_yeu: document.getElementById('ph_trichyeu').value,
        ngay_ban_hanh: document.getElementById('ph_ngay').value || null,
    };
    apiPost('/api/van-ban-di/' + _phatHanhId + '/phat-hanh/', data, () => {
        closeVBD('popupPhatHanh');
        window.location.reload();
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
                tbody.innerHTML += `<tr>
                    <td class="text-center">${i+1}</td>
                    <td class="text-center">${ls.thoi_gian}</td>
                    <td>${ls.nguoi_thuc_hien}</td>
                    <td class="text-center">${ls.ma_van_ban}</td>
                    <td>${ls.trich_yeu}</td>
                    <td>${ls.noi_dung}${ttHtml}</td>
                </tr>`;
            });
        }
        openVBD('historyOverlay');
    })
    .catch(() => {
        let tbody = document.querySelector('#historyOverlay .history-table-full tbody');
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center" style="color:#e74c3c;padding:20px;">Không tải được lịch sử</td></tr>';
        openVBD('historyOverlay');
    });
}
