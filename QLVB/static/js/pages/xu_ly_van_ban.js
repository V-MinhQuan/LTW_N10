function openModal(modalId) {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById(modalId).style.display = 'none';
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
    const soKyHieuInput = document.getElementById(`${prefix}-soKyHieu`);
    const trichYeuInput = document.getElementById(`${prefix}-trichYeu`);

    try {
        const response = await fetch(`/api/xu-ly-van-ban/document-details/?id=${id}&doc_type=${docType}`);
        const result = await response.json();
        console.log('API Result:', result);
        
        if (loadingDiv) loadingDiv.style.display = 'none';

        if (result.status === 'success') {
            const data = result.data;
            if (soKyHieuInput) soKyHieuInput.value = data.SoKyHieu;
            if (trichYeuInput) trichYeuInput.value = data.TrichYeu;
            
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

async function openModalC(modalId, docId, nguoiXuLy, docType) {
    document.getElementById('upd-nguoiXuLy').value = nguoiXuLy;
    document.getElementById('upd-soKyHieu').dataset.docType = docType;
    document.getElementById('upd-soKyHieu').dataset.docId = docId;
    
    await fetchDocumentDetails(docId, docType, 'upd');
    openModal(modalId);
}

async function openModalT(modalId, docId, docType) {
    document.getElementById('fwd-soKyHieu').dataset.docType = docType;
    document.getElementById('fwd-soKyHieu').dataset.docId = docId;

    await fetchDocumentDetails(docId, docType, 'fwd');
    openModal(modalId);
}

function openModalB(modalId, docId, docType) {
    // Bao cao doesn't need file preview for now, but we store IDs
    document.getElementById('rep-soKyHieu').dataset.docType = docType;
    document.getElementById('rep-soKyHieu').dataset.docId = docId;
    
    fetch(`/api/xu-ly-van-ban/document-details/?id=${docId}&doc_type=${docType}`)
        .then(res => res.json())
        .then(result => {
            if (result.status === 'success') {
                document.getElementById('rep-soKyHieu').value = result.data.SoKyHieu;
            }
        });

    openModal(modalId);
}

async function openModalP(modalId, docId, docType) {
    document.getElementById('asn-soKyHieu').dataset.docType = docType;
    document.getElementById('asn-soKyHieu').dataset.docId = docId;

    // Validate Han Xu Ly >= today
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
    let data = {};
    const csrftoken = getCookie('csrftoken');

    if (modalId === 'modalCapNhat') {
        url = '/api/xu-ly-van-ban/cap-nhat/';
        data = {
            so_ky_hieu: document.getElementById('upd-soKyHieu').value,
            trang_thai: document.getElementById('upd-trangThai').value,
            noi_dung: document.getElementById('upd-noiDung').value,
            doc_type: document.getElementById('upd-soKyHieu').dataset.docType
        };
        if (!data.trang_thai || !data.noi_dung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalChuyenTiep') {
        url = '/api/xu-ly-van-ban/chuyen-tiep/';
        const userSelect = document.getElementById('fwd-nguoiNhan');
        const selectedUsers = Array.from(userSelect.selectedOptions).map(opt => opt.value);
        data = {
            so_ky_hieu: document.getElementById('fwd-soKyHieu').value,
            user_id: selectedUsers,
            noi_dung: document.getElementById('fwd-noiDung').value,
            doc_type: document.getElementById('fwd-soKyHieu').dataset.docType
        };
        if (selectedUsers.length === 0 || !data.noi_dung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalBaoCao') {
        url = '/api/xu-ly-van-ban/bao-cao/';
        data = {
            so_ky_hieu: document.getElementById('rep-soKyHieu').value,
            loai_van_de: document.getElementById('rep-loaiVanDe').value,
            mo_ta: document.getElementById('rep-moTa').value,
            doc_type: document.getElementById('rep-soKyHieu').dataset.docType
        };
        if (!data.loai_van_de || !data.mo_ta) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalPhanCong') {
        url = '/api/xu-ly-van-ban/phan-cong/';
        const userSelect = document.getElementById('asn-nguoiXuLy');
        const selectedUsers = Array.from(userSelect.selectedOptions).map(opt => opt.value);
        data = {
            so_ky_hieu: document.getElementById('asn-soKyHieu').value,
            user_id: selectedUsers,
            han_xu_ly: document.getElementById('asn-thoiHan').value,
            ghi_chu: document.getElementById('asn-ghiChu').value,
            doc_type: document.getElementById('asn-soKyHieu').dataset.docType
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
    }

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
            alert(result.message);
            closeModal(modalId);
            location.reload(); // Tải lại trang để cập nhật dữ liệu
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Đã có lỗi xảy ra. Vui lòng thử lại!');
    }
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

    // Removed update modal drag and drop handlers since upload is disabled
});
