function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function openVBD(id) {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'block';
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = 'flex';
        // Prevent background scroll
        document.body.classList.add('vbd-modal-open');
        // Reset form if it's the Add popup to prevent pre-filled data artifacts
        if (id === 'popupAdd') {
            const form = modal.querySelector('form');
            if (form) form.reset();
            const uploadArea = document.getElementById('add_upload_area');
            const fileContainer = document.getElementById('add_tep_dinh_kem_container');
            if (uploadArea) uploadArea.style.setProperty('display', 'flex', 'important');
            if (fileContainer) fileContainer.style.display = 'none';
        }
    }
}

function closeVBD(id) {
    const modal = document.getElementById(id);
    if (modal) modal.style.display = 'none';
    const overlay = document.getElementById('modalOverlay');
    if (overlay) {
        // Only close overlay and restore scroll if no other modals are visible
        const visibleModals = document.querySelectorAll('.vbd-popup-overlay[style*="display: flex"], .vbd-popup-overlay[style*="display: block"]');
        if (visibleModals.length === 0) {
            overlay.style.display = 'none';
            document.body.classList.remove('vbd-modal-open');
        }
    }
}

window.addEventListener('click', function(event) {
    if (event.target.classList.contains('vbd-popup-overlay')) {
        closeVBD(event.target.id);
        if (event.target.id === 'historyOverlay') {
            openVBD('popupView');
        }
    }
    if (event.target.id === 'modalOverlay') {
        closeAllModals();
    }
});

// Lấy thông tin popup Xem
function xemVBD(id) {
    fetch(`/van-ban-den/${id}/xem/`)
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            const v = data.data;
            document.getElementById('view_trich_yeu').value = v.trich_yeu;
            document.getElementById('view_so_ky_hieu').value = v.so_ky_hieu;
            document.getElementById('view_loai_van_ban').value = v.loai_van_ban;
            document.getElementById('view_ngay_ban_hanh').value = v.ngay_ban_hanh;
            document.getElementById('view_ngay_nhan').value = v.ngay_nhan;
            document.getElementById('view_don_vi_gui').value = v.don_vi_ngoai_ten;
            if (document.getElementById('view_don_vi_trong')) {
                document.getElementById('view_don_vi_trong').value = v.don_vi_trong_ten;
            }
            
            const fileContainer = document.getElementById('view_tep_dinh_kem_container');
            const fileLink = document.getElementById('view_tep_dinh_kem_name');
            if (v.tep_dinh_kem) {
                fileContainer.style.display = 'block';
                fileLink.textContent = v.tep_name;
                fileLink.href = v.tep_dinh_kem;
            } else {
                fileContainer.style.display = 'none';
            }
            
            // Xử lý render Nội dung xử lý văn bản (động)
            const processRows = document.getElementById('view_process_rows');
            if (processRows) {
                if (v.qua_trinh_xu_ly && v.qua_trinh_xu_ly.length > 0) {
                    processRows.innerHTML = v.qua_trinh_xu_ly.map((item, index) => {
                        let actionClass = item.tag === 'Đang xử lý' ? ' vbd-process-action-highlight' : '';
                        let isLast = index === v.qua_trinh_xu_ly.length - 1;
                        const soNguoi = item.so_nguoi || 1;
                        const labelText = item.tag === 'Phản hồi' ? 'NGƯỜI PHẢN HỒI' : 'CHUYỂN TỚI';
                        
                        // Nếu nhiều người được phân công cùng lúc, hiển thị từng người trên 1 dòng con
                        let userHtml;
                        if (soNguoi > 1 && item.chuyen_toi) {
                            const names = item.chuyen_toi.split('\n');
                            const namesHtml = names.map(name => `<p class="vbd-p-name">${name.trim()}</p>`).join('');
                            userHtml = `
                                <p class="vbd-p-target">
                                    <i class="fas ${item.icon || 'fa-users'}"></i>
                                    <b>${labelText} (${soNguoi} người)</b>
                                </p>
                                ${namesHtml}
                            `;
                        } else {
                            userHtml = `
                                <p class="vbd-p-target">
                                    <i class="fas ${item.icon || 'fa-info-circle'}"></i>
                                    <b>${labelText}</b>
                                </p>
                                <p class="vbd-p-name">${item.chuyen_toi}</p>
                            `;
                        }
                        
                        return `
                          <div class="vbd-process-row">
                            <div class="vbd-process-tag-cell">
                                <div class="vbd-process-tag ${item.tag_class}">${item.tag}</div>
                                ${!isLast ? '<div class="vbd-process-line"></div>' : ''}
                            </div>
                            <div class="vbd-process-user">
                                ${userHtml}
                            </div>
                            <div class="vbd-process-action${actionClass}">${item.action || ""}</div>
                          </div>
                        `;
                    }).join('');
                } else {
                    processRows.innerHTML = '<div style="padding: 20px; text-align: center; color: #999; font-style: italic;">Chưa có thông tin xử lý điều hành</div>';
                }
            }
            
            // Gán id cho nút lịch sử (chỉ nút trong popupView)
            const historyBtn = document.querySelector('#popupView .btn-history');
            if (historyBtn) {
                historyBtn.dataset.id = id;
            }
            
            // Gán số ký hiệu cho nút sang xử lý
            const gotoBtn = document.getElementById('btn_goto_processing');
            if (gotoBtn) {
                gotoBtn.dataset.so_ky_hieu = v.so_ky_hieu;
            }
            
            openVBD('popupView');
        } else {
            App.showError(data.message);
        }
    });
}

// Bật form Thêm mới
function submitAddVBD() {
    const form = document.getElementById('formAddVBD');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    const formData = new FormData(form);
    
    fetch('/van-ban-den/them/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            App.showSuccess('Thêm thành công', () => {
                window.location.reload();
            });
        } else {
            App.showError(data.message);
        }
    }).catch(err => console.error(err));
}

// API get thông tin vào form Sửa
function suaVBD(id) {
    fetch(`/van-ban-den/${id}/xem/`)
    .then(res => res.json())
    .then(data => {
        if(data.status === 'success') {
            const v = data.data;
            document.getElementById('edit_id').value = id;
            document.getElementById('edit_trich_yeu').value = v.trich_yeu;
            document.getElementById('edit_so_ky_hieu').value = v.so_ky_hieu;
            document.getElementById('edit_loai_van_ban').value = v.loai_van_ban;
            document.getElementById('edit_ngay_ban_hanh').value = v.ngay_ban_hanh;
            document.getElementById('edit_ngay_nhan').value = v.ngay_nhan;
            document.getElementById('edit_don_vi_gui').value = v.don_vi_ngoai_ten === 'Chưa xác định' ? '' : v.don_vi_ngoai_ten;
            if (document.getElementById('edit_don_vi_trong')) {
                document.getElementById('edit_don_vi_trong').value = v.don_vi_trong_ten === 'Chưa xác định' ? '' : v.don_vi_trong_ten;
            }
            document.getElementById('edit_trang_thai').value = v.trang_thai;
            if (document.getElementById('edit_xoa_tep_dinh_kem')) {
                document.getElementById('edit_xoa_tep_dinh_kem').value = '0';
            }
            
            const editFileContainer = document.getElementById('edit_tep_dinh_kem_container');
            const editFileLink = document.getElementById('edit_tep_dinh_kem_name');
            if (editFileContainer && editFileLink) {
                if (v.tep_dinh_kem) {
                    editFileContainer.style.display = 'block';
                    editFileLink.textContent = v.tep_name;
                    editFileLink.href = v.tep_dinh_kem;
                } else {
                    editFileContainer.style.display = 'none';
                }
            }
            openVBD('popupEdit');
        } else {
            App.showError(data.message);
        }
    });
}

// Submit Sửa
function submitEditVBD() {
    const form = document.getElementById('formEditVBD');
    if (!form.checkValidity()) {
        form.reportValidity();
        return;
    }
    const id = document.getElementById('edit_id').value;
    const formData = new FormData(form);
    
    // Thu thập dữ liệu mới để cập nhật UI ngay lập tức
    const newData = {
        trich_yeu: document.getElementById('edit_trich_yeu').value,
        so_ky_hieu: document.getElementById('edit_so_ky_hieu').value,
        loai_vb: document.getElementById('edit_loai_van_ban').value,
        ngay_nhan: document.getElementById('edit_ngay_nhan').value,
        don_vi: document.getElementById('edit_don_vi_gui').value,
        trang_thai: document.getElementById('edit_trang_thai').value
    };

    fetch(`/van-ban-den/${id}/sua/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            App.showSuccess('Sửa thành công', () => {
                closeVBD('popupEdit');
                
                // Cập nhật dòng trong bảng mà không reload
                const row = document.querySelector(`tr[data-id="${id}"]`);
                if (row) {
                    const cells = row.cells;
                    // Cột 2: Số ký hiệu (link)
                    const link = cells[1].querySelector('a');
                    if (link) link.textContent = newData.so_ky_hieu;
                    
                    // Cột 3: Loại văn bản
                    cells[2].textContent = newData.loai_vb;
                    
                    // Cột 4: Trích yếu
                    cells[3].textContent = newData.trich_yeu;
                    cells[3].title = newData.trich_yeu;
                    
                    // Cột 5: Ngày nhận (Format lại date nếu cần, ở đây giả định yyyy-mm-dd -> dd/mm/yyyy)
                    if (newData.ngay_nhan) {
                        const parts = newData.ngay_nhan.split('-');
                        if (parts.length === 3) cells[4].textContent = `${parts[2]}/${parts[1]}/${parts[0]}`;
                    }
                    
                    // Cột 6: Đơn vị gửi
                    cells[5].textContent = newData.don_vi;
                    
                    // Cột 7: Trạng thái
                    const statusCell = cells[6];
                    if (newData.trang_thai === 'HOAN_THANH') {
                        statusCell.innerHTML = '<span class="status-pill pill-green">Hoàn thành</span>';
                    } else {
                        statusCell.innerHTML = '<span class="status-pill pill-orange">Đang xử lý</span>';
                    }
                    
                    // Thêm hiệu ứng highlight để báo hiệu đã cập nhật
                    row.style.transition = 'background-color 0.5s';
                    row.style.backgroundColor = '#e8f5e9';
                    setTimeout(() => {
                        row.style.backgroundColor = '';
                    }, 2000);
                }
            });
        } else {
            App.showError(data.message);
        }
    });
}

// Chức năng xóa văn bản đã bị gỡ bỏ theo yêu cầu nghiệp vụ

// Xem lịch sử hoạt động
function openHistory(id) {
    if (!id || id === 'undefined') {
        App.showError('Không xác định được ID văn bản để xem lịch sử.');
        return;
    }
    // Thêm timestamp để tránh cache
    fetch(`/van-ban-den/lich-su/?id=${id}&t=${new Date().getTime()}`)
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const tbody = document.getElementById('historyTableBodyDetail');
            tbody.innerHTML = '';
            
            if (data.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center">Không có lịch sử thay đổi</td></tr>';
            } else {
                data.data.forEach((item, index) => {
                    const tr = document.createElement('tr');
                    // Kết hợp Hành động vào Nội dung
                    const fullContent = `<b>${item.HanhDong}:</b> ${item.NoiDungThayDoi}`;
                    
                    tr.innerHTML = `
                        <td>${index + 1}</td>
                        <td>${item.ThoiGianCapNhat}</td>
                        <td>${item.NguoiThucHien}</td>
                        <td>${item.SoKyHieu}</td>
                        <td>${item.TrichYeu}</td>
                        <td>${fullContent}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            openVBD('historyOverlay');
        }
    });
}

document.addEventListener('DOMContentLoaded', function() {
    const addFileInput = document.getElementById('popupAddFileInput');
    const uploadArea = document.getElementById('add_upload_area');

    function xuLyChonFileVBDen(file) {
        if (!file) return;
        const container = document.getElementById('add_tep_dinh_kem_container');
        const nameEl = document.getElementById('add_tep_dinh_kem_name');
        const sizeEl = document.getElementById('add_tep_dinh_kem_size');
        if (nameEl) nameEl.textContent = file.name;
        if (sizeEl) sizeEl.textContent = (file.size / 1024).toFixed(2) + " KB";
        if (container) container.style.display = 'block';
        if (uploadArea) uploadArea.style.setProperty('display', 'none', 'important');

        // TỰ ĐỘNG KÍCH HOẠT QUÉT OCR & ĐIỀN THÔNG TIN TỨC THÌ
        quyetDuLieuOCRVanBanDen(file);
    }

    if (addFileInput) {
        addFileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                xuLyChonFileVBDen(this.files[0]);
            } else {
                const container = document.getElementById('add_tep_dinh_kem_container');
                if (container) container.style.display = 'none';
                if (uploadArea) uploadArea.style.setProperty('display', 'flex', 'important');
            }
        });
    }

    // Hỗ trợ kéo & thả (Drag & Drop) tệp tin vào vùng đính kèm
    if (uploadArea) {
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.style.borderColor = '#4f46e5';
                uploadArea.style.backgroundColor = '#eef2ff';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadArea.style.borderColor = '';
                uploadArea.style.backgroundColor = '';
            }, false);
        });

        uploadArea.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                const file = dt.files[0];
                if (addFileInput) {
                    try {
                        addFileInput.files = dt.files;
                    } catch (err) {}
                }
                xuLyChonFileVBDen(file);
            }
        }, false);
    }

    const editFileInput = document.getElementById('popupEditFileInput');
if(editFileInput) {
    editFileInput.addEventListener('change', function() {
        const container = document.getElementById('edit_new_tep_container');
        const nameEl = document.getElementById('edit_new_tep_name');
        const sizeEl = document.getElementById('edit_new_tep_size');
        const xoaFlag = document.getElementById('edit_xoa_tep_dinh_kem'); // 🔥 THÊM

        if(this.files.length > 0) {
            const file = this.files[0];
            nameEl.textContent = file.name;
            sizeEl.textContent = (file.size / 1024).toFixed(2) + " KB";
            container.style.display = 'block';

            if (xoaFlag) xoaFlag.value = '0';

            if(document.getElementById('edit_tep_dinh_kem_container')) {
                document.getElementById('edit_tep_dinh_kem_container').style.display = 'none';
            }
        } else {
            container.style.display = 'none';
            if(document.getElementById('edit_tep_dinh_kem_name') && document.getElementById('edit_tep_dinh_kem_name').getAttribute('href')) {
                document.getElementById('edit_tep_dinh_kem_container').style.display = 'block';
            }
        }
    });
}
    // Deletion buttons now use direct onclick handlers in HTML for maximum reliability
});

function removeEditFile(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }

    const container = document.getElementById('edit_tep_dinh_kem_container');
    if (container) container.style.display = 'none';

    const xoaFlag = document.getElementById('edit_xoa_tep_dinh_kem');
    if (xoaFlag) xoaFlag.value = '1';

    const fileInput = document.getElementById('popupEditFileInput');
    if (fileInput) fileInput.value = '';
}

function removeAddSelectedFile(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const fileInput = document.getElementById('popupAddFileInput');
    if (fileInput) fileInput.value = '';
    
    const container = document.getElementById('add_tep_dinh_kem_container');
    if (container) container.style.display = 'none';
    
    const uploadArea = document.getElementById('add_upload_area');
    if (uploadArea) uploadArea.style.setProperty('display', 'flex', 'important');
}

function removeEditSelectedFile(event) {
    if (event) {
        event.preventDefault();
        event.stopPropagation();
    }
    const fileInput = document.getElementById('popupEditFileInput');
    if (fileInput) fileInput.value = '';
    
    const container = document.getElementById('edit_new_tep_container');
    if (container) container.style.display = 'none';
    
    // When removing the newly selected file, we should also ensure the old file 
    // doesn't reappear if we want to support "no file at all"
    const xoaFlag = document.getElementById('edit_xoa_tep_dinh_kem');
    if (xoaFlag) xoaFlag.value = '1';
    
    const existingContainer = document.getElementById('edit_tep_dinh_kem_container');
    if (existingContainer) existingContainer.style.display = 'none';
}

function gotoProcessing(so_ky_hieu) {
    if (!so_ky_hieu) {
        App.showError('Không tìm thấy số ký hiệu văn bản.');
        return;
    }
    // Chuyển hướng sang trang xử lý với tham số tìm kiếm số ký hiệu
    window.location.href = '/xu-ly-van-ban/?so_ky_hieu=' + encodeURIComponent(so_ky_hieu);
}

// Áp dụng bộ lọc nâng cao
function applyFilterVBD() {
    const form = document.getElementById('filterFormVBD');
    if (!form) return;
    
    const formData = new FormData(form);
    const params = new URLSearchParams();
    
    // Giữ lại các tham số từ ô tìm kiếm nhanh nếu có
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.has('so_ky_hieu')) params.set('so_ky_hieu', urlParams.get('so_ky_hieu'));
    if (urlParams.has('trich_yeu')) params.set('trich_yeu', urlParams.get('trich_yeu'));
    if (urlParams.has('don_vi_trong')) params.set('don_vi_trong', urlParams.get('don_vi_trong'));
    
    // Thêm các tham số từ bộ lọc
    for (let [key, value] of formData.entries()) {
        if (value) {
            params.set(key, value);
        }
    }
    
    // Chuyển hướng
    window.location.href = window.location.pathname + '?' + params.toString();
}


// ================= CHUYỂN TIẾP VĂN BẢN LÊN GIÁM ĐỐC =================
function chuyenTiepGiamDoc(btn) {
    let id, soKyHieu;
    if (typeof btn === 'object' && btn !== null) {
        id = btn.getAttribute('data-id') || btn.dataset.id;
        soKyHieu = btn.getAttribute('data-so-ky-hieu') || btn.dataset.soKyHieu || '';
    } else {
        id = btn;
        soKyHieu = arguments[1] || '';
        btn = document.querySelector(`button[data-id="${id}"].btn-forward`);
    }

    if (!id) {
        if (window.App && window.App.showError) {
            window.App.showError('Không xác định được ID văn bản để chuyển tiếp!');
        } else {
            alert('Không xác định được ID văn bản để chuyển tiếp!');
        }
        return;
    }

    let originalHtml = '<i class="fas fa-share"></i>';
    if (btn) {
        originalHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    fetch('/api/van-ban-den/chuyen-tiep-giam-doc/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            van_ban_den_id: id,
            noi_dung: 'Kính trình Giám đốc xem xét và cho ý kiến chỉ đạo.'
        })
    })
    .then(res => res.json())
    .then(data => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }

        if (data.status === 'success') {
            const successMsg = data.message || `Đã chuyển tiếp văn bản '${soKyHieu}' lên Giám đốc thành công!`;
            if (window.App && window.App.showSuccess) {
                window.App.showSuccess(successMsg, () => {
                    const row = btn ? btn.closest('tr') : document.querySelector(`tr[data-id="${id}"]`);
                    if (row) {
                        row.style.transition = 'background-color 0.5s';
                        row.style.backgroundColor = '#f3e8ff';
                        setTimeout(() => { row.style.backgroundColor = ''; }, 3500);
                    }
                });
            } else {
                alert(successMsg);
            }
            window.dispatchEvent(new Event('notif-update'));
        } else {
            const errMsg = data.message || 'Chuyển tiếp thất bại!';
            if (window.App && window.App.showError) {
                window.App.showError(errMsg);
            } else {
                alert(errMsg);
            }
        }
    })
    .catch(err => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalHtml;
        }
        console.error('Lỗi chuyển tiếp Giám đốc:', err);
        if (window.App && window.App.showError) {
            window.App.showError('Có lỗi xảy ra khi kết nối máy chủ!');
        } else {
            alert('Có lỗi xảy ra khi kết nối máy chủ!');
        }
    });
}
function openChuyenTiepGD(id, soKyHieu) {
    chuyenTiepGiamDoc(id, soKyHieu);
}


// ==============================================================================
// GIAI ĐOẠN 3 (PHASE 3): AI OCR & TÓM TẮT THÔNG MINH BẰNG AI (VAN BAN DEN)
// ==============================================================================

let _currentViewVBDId = null;

// Hook vào hàm xemVBD để lưu ID và hiển thị tóm tắt AI nếu có
const _origXemVBD = window.xemVBD;
window.xemVBD = function(id) {
    _currentViewVBDId = id;
    fetch('/van-ban-den/' + id + '/xem/')
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const v = data.data;
            const aiSummaryContent = document.getElementById('ai_summary_content');
            const btnCopy = document.getElementById('btnCopyAISummary');
            if (aiSummaryContent) {
                if (v.tom_tat_ai) {
                    aiSummaryContent.innerHTML = v.tom_tat_ai;
                    if (btnCopy) btnCopy.style.display = 'inline-block';
                } else {
                    aiSummaryContent.innerHTML = `
                        <div style="color: #64748b; font-style: italic;">
                            <i class="fas fa-info-circle text-primary me-1"></i> Chưa có bản tóm tắt AI. Nhấn <b>"Phân tích AI"</b> để hệ thống tự động đọc và tóm tắt văn bản này.
                        </div>
                    `;
                    if (btnCopy) btnCopy.style.display = 'none';
                }
            }
        }
    })
    .catch(() => {});

    if (typeof _origXemVBD === 'function') {
        _origXemVBD(id);
    }
};

function _highlightOCRField(input) {
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

function quyetDuLieuOCRVanBanDen(customFile) {
    let file = customFile;
    if (!file) {
        const fileInput = document.getElementById('popupAddFileInput');
        if (fileInput && fileInput.files && fileInput.files[0]) {
            file = fileInput.files[0];
        }
    }

    if (!file) {
        alert("Vui lòng chọn hoặc kéo thả tệp văn bản trước khi quét OCR!");
        const fi = document.getElementById('popupAddFileInput');
        if (fi) fi.click();
        return;
    }

    const btn = document.getElementById('btnOcrScan');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang quét OCR...';
    }

    const badge = document.getElementById('ocr_status_badge');
    const badgeText = document.getElementById('ocr_status_text');
    if (badge) {
        badge.style.display = 'block';
        badge.style.background = '#eff6ff';
        badge.style.borderColor = '#93c5fd';
        badge.style.color = '#1e40af';
        badgeText.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> <b>AI OCR đang quét tệp:</b> Đang trích xuất Số ký hiệu, Loại văn bản, Ngày tháng, Cơ quan ban hành...';
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
            const form = document.getElementById('formAddVBD');
            if (form) {
                if (d.trich_yeu && form.elements['trich_yeu']) {
                    form.elements['trich_yeu'].value = d.trich_yeu;
                    _highlightOCRField(form.elements['trich_yeu']);
                }
                if (d.so_ky_hieu && form.elements['so_ky_hieu']) {
                    form.elements['so_ky_hieu'].value = d.so_ky_hieu;
                    _highlightOCRField(form.elements['so_ky_hieu']);
                }
                if (d.loai_van_ban && form.elements['loai_van_ban']) {
                    form.elements['loai_van_ban'].value = d.loai_van_ban;
                    _highlightOCRField(form.elements['loai_van_ban']);
                }
                if (d.ngay_ban_hanh && form.elements['ngay_ban_hanh']) {
                    form.elements['ngay_ban_hanh'].value = d.ngay_ban_hanh;
                    _highlightOCRField(form.elements['ngay_ban_hanh']);
                }
                if ((d.co_quan_ban_hanh || d.don_vi_ngoai_ten) && form.elements['don_vi_ngoai_id']) {
                    form.elements['don_vi_ngoai_id'].value = d.don_vi_ngoai_ten || d.co_quan_ban_hanh;
                    _highlightOCRField(form.elements['don_vi_ngoai_id']);
                }
            }

            if (badge) {
                badge.style.background = '#f0fdf4';
                badge.style.borderColor = '#86efac';
                badge.style.color = '#166534';
                badgeText.innerHTML = `✨ <b>AI OCR thành công:</b> Đã tự động điền các trường văn bản (Số: <b>${d.so_ky_hieu || 'N/A'}</b> | Loại: <b>${d.loai_van_ban}</b> | Ngày: <b>${d.ngay_ban_hanh}</b>)!`;
            }
            if (window.App && App.showSuccess) {
                App.showSuccess("AI đã quét OCR và tự động điền các ô dữ liệu thành công!");
            }
        } else {
            if (badge) {
                badge.style.background = '#fef2f2';
                badge.style.borderColor = '#fca5a5';
                badge.style.color = '#991b1b';
                badgeText.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> ${res.message || 'Không thể quét OCR nội dung văn bản này'}`;
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (badge) {
            badge.style.background = '#fef2f2';
            badge.style.borderColor = '#fca5a5';
            badge.style.color = '#991b1b';
            badgeText.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Lỗi kết nối khi quét OCR!';
        }
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    });
}

function yeuCauTomTatAI(docType) {
    const id = _currentViewVBDId;
    if (!id) {
        alert("Không tìm thấy mã văn bản cần tóm tắt!");
        return;
    }

    const contentDiv = document.getElementById('ai_summary_content');
    const btn = document.getElementById('btnRunAISummary');
    const btnText = document.getElementById('btnRunAISummaryText');
    const btnCopy = document.getElementById('btnCopyAISummary');

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

    fetch('/api/ai/' + id + '/summarize/?type=' + (docType || 'den') + '&refresh=1', {
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

function saoChepTomTatAI() {
    const btnCopy = document.getElementById('btnCopyAISummary');
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
