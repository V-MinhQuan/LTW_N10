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

async function fetchDocumentDetails(id, docType, prefix) {
    console.log(`Fetching details for ${docType} ID: ${id} with prefix: ${prefix}`);
    const fileCard = document.getElementById(`${prefix}-fileCard`);
    const noFile = document.getElementById(`${prefix}-noFile`);
    const loadingDiv = document.getElementById(`${prefix}-loading`);
    
    // Reset UI to loading state
    if (fileCard) fileCard.style.display = 'none';
    if (noFile) noFile.style.display = 'none';
    if (loadingDiv) loadingDiv.style.display = 'flex';

    const fileNameElementId = prefix === 'upd' ? 'upd-fileNameSpan' : `${prefix}-fileName`;
    const fileNameSpan = document.getElementById(fileNameElementId);
    const fileLink = document.getElementById(`${prefix}-fileLink`);

    try {
        const response = await fetch(`/api/xu-ly-van-ban/document-details/?id=${id}&doc_type=${docType}`);
        const result = await response.json();
        console.log('API Result:', result);
        
        if (loadingDiv) loadingDiv.style.display = 'none';

        if (result.status === 'success') {
            const data = result.data;
            
            if (data.TepDinhKemUrl) {
                console.log('Found file URL:', data.TepDinhKemUrl);
                if (fileLink) fileLink.href = data.TepDinhKemUrl;
                let displayFileName = data.TepDinhKemName;
                if (displayFileName && displayFileName.includes('/')) {
                    displayFileName = displayFileName.split('/').pop();
                }
                if (fileNameSpan) fileNameSpan.textContent = displayFileName || 'Tệp đính kèm';
                if (fileCard) fileCard.style.display = 'flex';
                if (noFile) noFile.style.display = 'none';
            } else {
                console.log('No file URL returned.');
                if (fileCard) fileCard.style.display = 'none';
                if (noFile) noFile.style.display = 'flex';
            }
        } else {
            console.error('Error fetching doc details:', result.message);
            if (noFile) noFile.style.display = 'flex';
        }
    } catch (error) {
        console.error('Fetch error:', error);
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (noFile) noFile.style.display = 'flex';
    }
}

async function openModalC(modalId, docId, soKyHieu, nguoiXuLy, docType, fileUrl) {
    const elSo = document.getElementById('upd-soKyHieu');
    const elNguoi = document.getElementById('upd-nguoiXuLy');
    const elType = document.getElementById('upd-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elNguoi) elNguoi.value = nguoiXuLy;
    if (elType) elType.value = docType;

    const newContainer = document.getElementById('upd-file-list-new');
    if (newContainer) newContainer.style.display = 'none';
    document.getElementById('upd-file').value = '';

    await fetchDocumentDetails(docId, docType, 'upd');
    openModal(modalId);
}

async function openModalT(modalId, docId, soKyHieu, docType) {
    const elSo = document.getElementById('fwd-soKyHieu');
    const elType = document.getElementById('fwd-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;

    await fetchDocumentDetails(docId, docType, 'fwd');
    openModal(modalId);
}

function openModalB(modalId, docId, soKyHieu, docType) {
    const elSo = document.getElementById('rep-soKyHieu');
    const elType = document.getElementById('rep-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;
    
    openModal(modalId);
}

async function openModalP(modalId, docId, soKyHieu, trichYeu, docType) {
    const elSo = document.getElementById('asn-soKyHieu');
    const elTrich = document.getElementById('asn-trichYeu');
    const elType = document.getElementById('asn-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elTrich) elTrich.value = trichYeu;
    if (elType) elType.value = docType;

    const dateInput = document.getElementById('asn-thoiHan');
    if (dateInput) {
        const today = new Date().toISOString().split('T')[0];
        dateInput.min = today;
    }

    await fetchDocumentDetails(docId, docType, 'asn');
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
        const userSelect = document.getElementById('fwd-nguoiNhan');
        const selectedUsers = Array.from(userSelect.selectedOptions).map(opt => opt.value);
        const data = {
            so_ky_hieu: document.getElementById('fwd-soKyHieu').value,
            don_vi_id: selectedUsers,
            noi_dung: document.getElementById('fwd-noiDung').value,
            doc_type: document.getElementById('fwd-docType').value
        };
        if (selectedUsers.length === 0 || !data.noi_dung) {
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
        const todayStr = new Date().toISOString().split('T')[0];
        if (data.han_xu_ly < todayStr) {
            alert('Thời hạn xử lý không được nhỏ hơn ngày hiện tại!');
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
            placeholder: true,
            placeholderValue: 'Chọn người xử lý',
            searchPlaceholderValue: 'Tìm kiếm người xử lý...'
        });
    }

    // Khởi tạo Choices.js cho chọn nhiều người - Chuyển tiếp
    const fwdUserSelect = document.getElementById('fwd-nguoiNhan');
    if (fwdUserSelect && typeof Choices !== 'undefined') {
        new Choices(fwdUserSelect, {
            removeItemButton: true,
            placeholder: true,
            placeholderValue: 'Chọn người nhận',
            searchPlaceholderValue: 'Tìm kiếm người nhận...'
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
                // Ẩn tệp cũ nếu người dùng chọn tệp mới
                const existingContainer = document.getElementById('upd-fileCard');
                if (existingContainer) existingContainer.style.display = 'none';
                const existingNoFile = document.getElementById('upd-noFile');
                if (existingNoFile) existingNoFile.style.display = 'none';
            } else {
                if (newContainer) newContainer.style.display = 'none';
            }
        });
    }
});
