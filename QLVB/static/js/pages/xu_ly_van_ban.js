function openModal(modalId) {
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'block';
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'block';
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.style.display = 'none';
    const overlay = document.getElementById('modalOverlay');
    if (overlay) overlay.style.display = 'none';
}

function openModalC(modalId, soKyHieu, nguoiXuLy, docType, fileUrl) {
    const elSo = document.getElementById('upd-soKyHieu');
    const elNguoi = document.getElementById('upd-nguoiXuLy');
    const elType = document.getElementById('upd-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elNguoi) elNguoi.value = nguoiXuLy;
    if (elType) elType.value = docType;

    // Hiển thị tệp hiện có nếu có
    const existingContainer = document.getElementById('upd-file-list-existing');
    const existingLink = document.getElementById('upd-existing-filename');
    const newContainer = document.getElementById('upd-file-list-new');
    
    if (fileUrl && existingContainer && existingLink) {
        existingLink.href = fileUrl;
        existingLink.textContent = fileUrl.split('/').pop();
        existingContainer.style.display = 'block';
    } else if (existingContainer) {
        existingContainer.style.display = 'none';
    }
    
    if (newContainer) newContainer.style.display = 'none';
    document.getElementById('upd-file').value = '';

    openModal(modalId);
}

function openModalT(modalId, soKyHieu, docType) {
    const elSo = document.getElementById('fwd-soKyHieu');
    const elType = document.getElementById('fwd-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;
    openModal(modalId);
}

function openModalB(modalId, soKyHieu, docType) {
    const elSo = document.getElementById('rep-soKyHieu');
    const elType = document.getElementById('rep-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;
    openModal(modalId);
}

function openModalP(modalId, soKyHieu, trichYeu, docType) {
    const elSo = document.getElementById('asn-soKyHieu');
    const elTrich = document.getElementById('asn-trichYeu');
    const elType = document.getElementById('asn-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elTrich) elTrich.value = trichYeu;
    if (elType) elType.value = docType;
    openModal(modalId);
}

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

async function saveAndClose(modalId) {
    let url = '';
    const formData = new FormData();
    const csrftoken = getCookie('csrftoken');

    if (modalId === 'modalCapNhat') {
        url = '/api/xu-ly-van-ban/cap-nhat/';
        const soKyHieu = document.getElementById('upd-soKyHieu').value;
        const trangThai = document.getElementById('upd-trangThai').value;
        const noiDung = document.getElementById('upd-noiDung').value;
        const docType = document.getElementById('upd-docType').value;
        const fileInput = document.getElementById('upd-file');

        if (!trangThai || !noiDung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }

        formData.append('so_ky_hieu', soKyHieu);
        formData.append('trang_thai', trangThai);
        formData.append('noi_dung', noiDung);
        formData.append('doc_type', docType);
        if (fileInput.files.length > 0) {
            formData.append('tep_dinh_kem', fileInput.files[0]);
        }
    } else if (modalId === 'modalChuyenTiep') {
        url = '/api/xu-ly-van-ban/chuyen-tiep/';
        const data = {
            so_ky_hieu: document.getElementById('fwd-soKyHieu').value,
            don_vi_id: document.getElementById('fwd-nguoiNhan').value,
            noi_dung: document.getElementById('fwd-noiDung').value,
            doc_type: document.getElementById('fwd-docType').value
        };
        if (!data.don_vi_id || !data.noi_dung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
        // Giữ nguyên JSON cho các modal chưa yêu cầu file
        return postJson(url, data, modalId);

    } else if (modalId === 'modalBaoCao') {
        url = '/api/xu-ly-van-ban/bao-cao/';
        const data = {
            so_ky_hieu: document.getElementById('rep-soKyHieu').value,
            loai_van_de: document.getElementById('rep-loaiVanDe').value,
            mo_ta: document.getElementById('rep-moTa').value,
            doc_type: document.getElementById('rep-docType').value
        };
        if (!data.loai_van_de || !data.mo_ta) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
        return postJson(url, data, modalId);

    } else if (modalId === 'modalPhanCong') {
        url = '/api/xu-ly-van-ban/phan-cong/';
        const userSelect = document.getElementById('asn-nguoiXuLy');
        const selectedUsers = Array.from(userSelect.selectedOptions).map(opt => opt.value);
        const data = {
            so_ky_hieu: document.getElementById('asn-soKyHieu').value,
            user_id: selectedUsers,
            han_xu_ly: document.getElementById('asn-thoiHan').value,
            ghi_chu: document.getElementById('asn-ghiChu').value,
            doc_type: document.getElementById('asn-docType').value
        };
        if (selectedUsers.length === 0 || !data.han_xu_ly) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
        return postJson(url, data, modalId);
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrftoken
            },
            body: formData
        });

        const result = await response.json();
        if (result.status === 'success') {
            closeModal(modalId);
            App.showSuccess(result.message || 'Thao tác thành công', () => {
                location.reload();
            });
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Đã có lỗi xảy ra. Vui lòng thử lại!');
    }
}

// Hàm bổ trợ gửi JSON
async function postJson(url, data, modalId) {
    const csrftoken = getCookie('csrftoken');
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken
            },
            body: JSON.stringify(data)
        });
        const result = await response.json();
        if (result.status === 'success') {
            closeModal(modalId);
            App.showSuccess(result.message || 'Thao tác thành công', () => {
                location.reload();
            });
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (e) { console.error(e); alert('Lỗi hệ thống!'); }
}

function removeSelectedFileUpd() {
    const fileInput = document.getElementById('upd-file');
    if (fileInput) fileInput.value = '';
    const newContainer = document.getElementById('upd-file-list-new');
    if (newContainer) newContainer.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', function() {
    // Khởi tạo Choices.js cho chọn nhiều người
    const userSelect = document.getElementById('asn-nguoiXuLy');
    if (userSelect && typeof Choices !== 'undefined') {
        new Choices(userSelect, {
            removeItemButton: true,
            placeholderValue: '--- Chọn người xử lý ---',
            searchPlaceholderValue: 'Tìm kiếm người xử lý...'
        });
    }

    // For Phân công modal
    const fileInputAsn = document.getElementById('asn-file');
    const fileNameDisplayAsn = document.getElementById('asn-fileName');
    const uploadAreaAsn = document.getElementById('uploadFileArea');

    if (fileInputAsn && fileNameDisplayAsn) {
        fileInputAsn.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileNameDisplayAsn.textContent = 'Đã chọn tệp: ' + this.files[0].name;
            } else {
                fileNameDisplayAsn.textContent = '';
            }
        });
    }

    if (uploadAreaAsn && fileInputAsn) {
        uploadAreaAsn.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadAreaAsn.style.backgroundColor = '#e6f3ff';
        });

        uploadAreaAsn.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadAreaAsn.style.backgroundColor = '#f8fbff';
        });

        uploadAreaAsn.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadAreaAsn.style.backgroundColor = '#f8fbff';
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInputAsn.files = e.dataTransfer.files;
                fileInputAsn.dispatchEvent(new Event('change'));
            }
        });
    }

    // For Cập nhật modal
    const fileInputUpd = document.getElementById('upd-file');
    const newContainer = document.getElementById('upd-file-list-new');
    const newFilename = document.getElementById('upd-new-filename');

    if (fileInputUpd) {
        fileInputUpd.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                if (newFilename) newFilename.textContent = this.files[0].name;
                if (newContainer) newContainer.style.display = 'block';
                // Ẩn tệp cũ nếu người dùng chọn tệp mới (tùy chọn UI)
                const existingContainer = document.getElementById('upd-file-list-existing');
                if (existingContainer) existingContainer.style.display = 'none';
            } else {
                if (newContainer) newContainer.style.display = 'none';
            }
        });
    }
});
