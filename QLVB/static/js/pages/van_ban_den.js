function openVBD(id) {
    document.getElementById(id).style.display = 'flex';
}
function closeVBD(id) {
    document.getElementById(id).style.display = 'none';
}

window.onclick = function(event) {
    if (event.target.classList.contains('vbd-popup-overlay')) {
        const id = event.target.id;
        event.target.style.display = "none";
        if (id === 'historyOverlay') {
            openVBD('popupView');
        }
    }
}

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
            
            const fileContainer = document.getElementById('view_tep_dinh_kem_container');
            const fileLink = document.getElementById('view_tep_dinh_kem_name');
            if (v.tep_dinh_kem) {
                fileContainer.style.display = 'block';
                fileLink.textContent = v.tep_name;
                fileLink.href = v.tep_dinh_kem;
            } else {
                fileContainer.style.display = 'none';
            }
            
            // Gán id để nút lịch sử biết
            document.querySelector('.btn-history').dataset.id = id;
            
            openVBD('popupView');
        } else {
            alert(data.message);
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
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Thêm thành công');
            window.location.reload();
        } else {
            alert('Lỗi: ' + data.message);
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
            document.getElementById('edit_don_vi_gui').value = v.don_vi_ngoai_id;
            
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
            alert(data.message);
        }
    });
}

// Submit Sửa
function submitEditVBD() {
    const form = document.getElementById('formEditVBD');
    const id = document.getElementById('edit_id').value;
    const formData = new FormData(form);
    
    fetch(`/van-ban-den/${id}/sua/`, {
        method: 'POST',
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            alert('Sửa thành công');
            window.location.reload();
        } else {
            alert('Lỗi: ' + data.message);
        }
    });
}

// Xóa
function xoaVBD(id) {
    document.getElementById('popupRemove').dataset.id = id;
    openVBD('popupRemove');
}

function submitXoaVBD() {
    const id = document.getElementById('popupRemove').dataset.id;
    fetch(`/van-ban-den/${id}/xoa/`, {
        method: 'POST'
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            window.location.reload();
        } else {
            alert('Lỗi khi xóa');
        }
    });
}

// Xem lịch sử hoạt động
function openHistory(id) {
    fetch(`/van-ban-den/lich-su/?id=${id}`)
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success') {
            const tbody = document.getElementById('historyTableBody');
            tbody.innerHTML = '';
            
            if (data.data.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" class="text-center">Không có lịch sử thay đổi</td></tr>';
            } else {
                data.data.forEach(item => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td class="text-center">${item.ThoiGianCapNhat}</td>
                        <td>${item.NguoiThucHien}</td>
                        <td><span class="status-pill pill-blue">${item.HanhDong}</span></td>
                        <td>${item.NoiDungThayDoi}</td>
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
            if(this.files.length > 0) {
                const file = this.files[0];
                nameEl.textContent = file.name;
                sizeEl.textContent = (file.size / 1024).toFixed(2) + " KB";
                container.style.display = 'block';
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
});

function removeEditFile() {
    if(confirm('Bạn có chắc chắn muốn xóa tệp đính kèm này không?')) {
        document.getElementById('edit_tep_dinh_kem_container').style.display = 'none';
        if(document.getElementById('edit_xoa_tep_dinh_kem')) {
            document.getElementById('edit_xoa_tep_dinh_kem').value = '1';
        }
    }
}

function removeAddSelectedFile() {
    document.getElementById('popupAddFileInput').value = '';
    document.getElementById('add_tep_dinh_kem_container').style.display = 'none';
    const uploadArea = document.getElementById('add_upload_area');
    if (uploadArea) uploadArea.style.setProperty('display', 'flex', 'important');
}

function removeEditSelectedFile() {
    document.getElementById('popupEditFileInput').value = '';
    document.getElementById('edit_new_tep_container').style.display = 'none';
    if(document.getElementById('edit_tep_dinh_kem_name') && document.getElementById('edit_tep_dinh_kem_name').getAttribute('href')) {
        document.getElementById('edit_tep_dinh_kem_container').style.display = 'block';
    }
}
