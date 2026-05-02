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
                window.location.reload();
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
    if(addFileInput) {
        addFileInput.addEventListener('change', function() {
            const container = document.getElementById('add_tep_dinh_kem_container');
            const nameEl = document.getElementById('add_tep_dinh_kem_name');
            const sizeEl = document.getElementById('add_tep_dinh_kem_size');
            const uploadArea = document.getElementById('add_upload_area');
            if(this.files.length > 0) {
                const file = this.files[0];
                nameEl.textContent = file.name;
                sizeEl.textContent = (file.size / 1024).toFixed(2) + " KB";
                container.style.display = 'block';
                if (uploadArea) uploadArea.style.setProperty('display', 'none', 'important');
            } else {
                container.style.display = 'none';
                if (uploadArea) uploadArea.style.setProperty('display', 'flex', 'important');
            }
        });
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
