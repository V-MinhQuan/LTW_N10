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

    if (loadingDiv) loadingDiv.style.display = 'block';
    if (fileCard) fileCard.style.display = 'none';
    if (noFile) noFile.style.display = 'none';

    try {
        const response = await fetch(`/api/xu-ly-van-ban/document-details/?id=${id}&doc_type=${docType}`);
        const result = await response.json();
        
        if (loadingDiv) loadingDiv.style.display = 'none';

        if (result.status === 'success' && result.data.TepDinhKemUrl) {
            if (fileCard) {
                fileCard.style.display = 'block';
                const link = document.getElementById(`${prefix}-fileLink`);
                if (link) {
                    link.href = result.data.TepDinhKemUrl;
                    // Lấy phần tên tệp từ đường dẫn
                    const fullName = result.data.TepDinhKemName || 'Tài liệu đính kèm';
                    const fileName = fullName.split('/').pop();
                    link.innerText = fileName;
                }
            }
        } else {
            if (noFile) noFile.style.display = 'block';
        }
    } catch (e) {
        console.error(e);
        if (loadingDiv) loadingDiv.style.display = 'none';
        if (noFile) noFile.style.display = 'block';
    }
}

let choicesInstances = {};

function initChoices(elementId, placeholder) {
    const el = document.getElementById(elementId);
    if (el && typeof Choices !== 'undefined' && !choicesInstances[elementId]) {
        const instance = new Choices(el, {
            removeItemButton: true,
            placeholder: true,
            placeholderValue: placeholder || 'Chọn...',
            searchPlaceholderValue: 'Tìm kiếm...',
            itemSelectText: '',
            noResultsText: 'Không tìm thấy kết quả',
            noChoicesText: 'Không còn lựa chọn nào'
        });
        choicesInstances[elementId] = instance;

        const updatePlaceholder = () => {
            const selectedCount = instance.getValue(true).length;
            const container = el.closest('.choices');
            if (container) {
                const input = container.querySelector('.choices__input');
                if (input) {
                    if (selectedCount > 0) {
                        input.placeholder = '';
                        input.style.setProperty('min-width', '20px', 'important');
                        input.style.width = '20px';
                    } else {
                        input.placeholder = placeholder || 'Chọn...';
                        input.style.setProperty('min-width', '180px', 'important');
                    }
                }
            }
        };

        el.addEventListener('addItem', () => setTimeout(updatePlaceholder, 50));
        el.addEventListener('removeItem', () => setTimeout(updatePlaceholder, 50));
        el.addEventListener('change', () => setTimeout(updatePlaceholder, 50));
        
        setTimeout(updatePlaceholder, 200);

        if (elementId === 'asn-nguoiXuLy' || elementId === 'fwd-nguoiNhan') {
            loadUsersToChoices(instance);
        }
    }
}

async function loadUsersToChoices(instance) {
    try {
        const response = await fetch('/api/nguoi-dung/list/?page_size=all');
        const result = await response.json();
        if (result.status === 'success') {
            const choices = result.data.map(u => ({
                value: u.id,
                label: u.fullname,
                selected: false,
                disabled: u.status === 'INACTIVE'
            }));
            instance.setChoices(choices, 'value', 'label', true);
        }
    } catch (e) {
        console.error('Error loading users:', e);
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
    const fileInput = document.getElementById('upd-file');
    if (fileInput) fileInput.value = '';

    await fetchDocumentDetails(docId, docType, 'upd');
    openModal(modalId);
}

async function openModalT(modalId, docId, soKyHieu, docType) {
    const elSo = document.getElementById('fwd-soKyHieu');
    const elType = document.getElementById('fwd-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;

    initChoices('fwd-nguoiNhan', 'Chọn người nhận');

    const newContainer = document.getElementById('fwd-file-list-new');
    if (newContainer) newContainer.style.display = 'none';

    await fetchDocumentDetails(docId, docType, 'fwd');
    openModal(modalId);
}

function openModalB(modalId, docId, soKyHieu, docType) {
    const elSo = document.getElementById('rep-soKyHieu');
    const elType = document.getElementById('rep-docType');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;

    const newContainer = document.getElementById('rep-file-list-new');
    if (newContainer) newContainer.style.display = 'none';

    fetchDocumentDetails(docId, docType, 'rep');
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
        dateInput.value = today;
    }

    initChoices('asn-nguoiXuLy', 'Chọn người xử lý');
    
    const newContainer = document.getElementById('asn-file-list-new');
    if (newContainer) newContainer.style.display = 'none';
    const fileInput = document.getElementById('asn-file');
    if (fileInput) fileInput.value = '';

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
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            formData.append('tep_dinh_kem', fileInput.files[0]);
        }
    } else if (modalId === 'modalChuyenTiep') {
        url = '/api/xu-ly-van-ban/chuyen-tiep/';
        const userSelect = document.getElementById('fwd-nguoiNhan');
        const selectedUsers = choicesInstances['fwd-nguoiNhan'] ? choicesInstances['fwd-nguoiNhan'].getValue(true) : [];
        const soKyHieu = document.getElementById('fwd-soKyHieu').value;
        const noiDung = document.getElementById('fwd-noiDung').value;
        const docType = document.getElementById('fwd-docType').value;
        const fileInput = document.getElementById('fwd-file');

        if (selectedUsers.length === 0 || !noiDung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }

        formData.append('so_ky_hieu', soKyHieu);
        selectedUsers.forEach(id => formData.append('user_id', id));
        formData.append('noi_dung', noiDung);
        formData.append('doc_type', docType);
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            formData.append('tep_dinh_kem', fileInput.files[0]);
        }
    } else if (modalId === 'modalBaoCao') {
        url = '/api/xu-ly-van-ban/bao-cao/';
        const soKyHieu = document.getElementById('rep-soKyHieu').value;
        const loaiVanDe = document.getElementById('rep-loaiVanDe').value;
        const moTa = document.getElementById('rep-moTa').value;
        const docType = document.getElementById('rep-docType').value;
        const recipientId = document.getElementById('rep-nguoiNhan').value;
        const fileInput = document.getElementById('rep-file');

        if (!loaiVanDe || !moTa || !recipientId) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc (Loại vấn đề, Mô tả, Người nhận)!');
            return;
        }

        formData.append('so_ky_hieu', soKyHieu);
        formData.append('loai_van_de', loaiVanDe);
        formData.append('mo_ta', moTa);
        formData.append('doc_type', docType);
        formData.append('recipient_id', recipientId);
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            formData.append('tep_dinh_kem', fileInput.files[0]);
        }
    } else if (modalId === 'modalPhanCong') {
        url = '/api/xu-ly-van-ban/phan-cong/';
        const userSelect = document.getElementById('asn-nguoiXuLy');
        const selectedUsers = choicesInstances['asn-nguoiXuLy'] ? choicesInstances['asn-nguoiXuLy'].getValue(true) : [];
        const soKyHieu = document.getElementById('asn-soKyHieu').value;
        const hanXuLy = document.getElementById('asn-thoiHan').value;
        const ghiChu = document.getElementById('asn-ghiChu').value;
        const docType = document.getElementById('asn-docType').value;
        const fileInput = document.getElementById('asn-file');

        if (selectedUsers.length === 0 || !hanXuLy) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }

        formData.append('so_ky_hieu', soKyHieu);
        selectedUsers.forEach(id => formData.append('user_id', id));
        formData.append('han_xu_ly', hanXuLy);
        formData.append('ghi_chu', ghiChu);
        formData.append('doc_type', docType);
        if (fileInput && fileInput.files && fileInput.files.length > 0) {
            formData.append('tep_dinh_kem', fileInput.files[0]);
        }
    }

    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'X-CSRFToken': csrftoken },
            body: formData
        });
        const result = await response.json();
        if (result.status === 'success') {
            closeModal(modalId);
            if (typeof App !== 'undefined' && App.showSuccess) {
                App.showSuccess(result.message || 'Thao tác thành công', () => location.reload());
            } else {
                alert(result.message || 'Thao tác thành công');
                location.reload();
            }
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (e) {
        console.error(e);
        alert('Lỗi hệ thống!');
    }
}

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
            if (typeof App !== 'undefined' && App.showSuccess) {
                App.showSuccess(result.message || 'Thao tác thành công', () => location.reload());
            } else {
                alert(result.message || 'Thao tác thành công');
                location.reload();
            }
        } else {
            alert('Lỗi: ' + result.message);
        }
    } catch (e) { console.error(e); alert('Lỗi hệ thống!'); }
}

function removeSelectedFileAsn() {
    const fileInput = document.getElementById('asn-file');
    if (fileInput) fileInput.value = '';
    const container = document.getElementById('asn-file-list-new');
    if (container) container.style.display = 'none';
}

function removeSelectedFileUpd() {
    const fileInput = document.getElementById('upd-file');
    if (fileInput) fileInput.value = '';
    const container = document.getElementById('upd-file-list-new');
    if (container) container.style.display = 'none';
}

function removeSelectedFileFwd() {
    const fileInput = document.getElementById('fwd-file');
    if (fileInput) fileInput.value = '';
    const container = document.getElementById('fwd-file-list-new');
    if (container) container.style.display = 'none';
}

function removeSelectedFileRep() {
    const fileInput = document.getElementById('rep-file');
    if (fileInput) fileInput.value = '';
    const container = document.getElementById('rep-file-list-new');
    if (container) container.style.display = 'none';
}

document.addEventListener('DOMContentLoaded', () => {
    const fileInputs = ['asn-file', 'upd-file', 'fwd-file', 'rep-file'];
    fileInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener('change', function() {
                const prefix = id.split('-')[0];
                const fileList = document.getElementById(`${prefix}-file-list-new`);
                const fileNameSpan = document.getElementById(`${prefix}-new-filename`);
                if (this.files && this.files.length > 0) {
                    if (fileNameSpan) fileNameSpan.innerText = this.files[0].name;
                    if (fileList) fileList.style.display = 'block';
                } else {
                    if (fileList) fileList.style.display = 'none';
                }
            });
        }
    });
});

// --- Logic xử lý báo cáo mới ---

async function openModalListReports() {
    try {
        const response = await fetch('/api/xu-ly-van-ban/danh-sach-bao-cao/');
        const result = await response.json();
        if (result.status === 'success') {
            const body = document.getElementById('report-list-body');
            body.innerHTML = '';
            if (result.data.length === 0) {
                body.innerHTML = '<tr><td colspan="5" class="text-center">Không có báo cáo nào cần xử lý.</td></tr>';
            } else {
                result.data.forEach(r => {
                    const row = `
                        <tr>
                            <td>${r.nguoi_bao_cao}</td>
                            <td><b>${r.so_ky_hieu}</b><br><small>${r.trich_yeu}</small></td>
                            <td>${r.loai_bao_cao}</td>
                            <td>${r.ngay_bao_cao}</td>
                            <td>
                                <button class="btn btn-primary btn-sm" onclick='openModalHandlingReport(${JSON.stringify(r)})'>
                                    Xử lý
                                </button>
                            </td>
                        </tr>
                    `;
                    body.insertAdjacentHTML('beforeend', row);
                });
            }
            openModal('modalDanhSachBaoCao');
        }
    } catch (e) {
        console.error(e);
        alert('Không thể tải danh sách báo cáo!');
    }
}

function openModalHandlingReport(r) {
    // Đóng modal danh sách trước
    closeModal('modalDanhSachBaoCao');
    
    document.getElementById('xl-reportId').value = r.id;
    document.getElementById('xl-soKyHieu').innerText = r.so_ky_hieu;
    document.getElementById('xl-ghiChu').innerText = r.ghi_chu;
    document.getElementById('xl-noiDungXuLy').value = '';
    document.getElementById('xl-huongXuLy').value = 'SUA';
    toggleRecipientSelect();
    
    openModal('modalThucHienXuLyBaoCao');
}

function toggleRecipientSelect() {
    const action = document.getElementById('xl-huongXuLy').value;
    const div = document.getElementById('div-new-recipient');
    if (action === 'CHUYEN') {
        div.style.display = 'block';
    } else {
        div.style.display = 'none';
    }
}

async function confirmXuLyBaoCao() {
    const reportId = document.getElementById('xl-reportId').value;
    const action = document.getElementById('xl-huongXuLy').value;
    const noiDung = document.getElementById('xl-noiDungXuLy').value;
    const newRecipientId = document.getElementById('xl-newRecipient').value;
    
    if (!noiDung) {
        alert('Vui lòng nhập nội dung phản hồi xử lý!');
        return;
    }
    
    if (action === 'CHUYEN' && !newRecipientId) {
        alert('Vui lòng chọn người nhận mới để chuyển tiếp báo cáo!');
        return;
    }
    
    const data = {
        report_id: reportId,
        action: action,
        noi_dung: noiDung,
        new_recipient_id: newRecipientId
    };
    
    await postJson('/api/xu-ly-van-ban/thuc-hien-xu-ly-bao-cao/', data, 'modalThucHienXuLyBaoCao');
}

function rejectReport() {
    const noiDung = document.getElementById('xl-noiDungXuLy').value;
    if (!noiDung) {
        alert('Vui lòng nhập lý do từ chối vào ô nội dung phản hồi!');
        return;
    }
    document.getElementById('xl-huongXuLy').value = 'TU_CHOI';
    confirmXuLyBaoCao();
}
