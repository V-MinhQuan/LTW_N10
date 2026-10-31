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

        if (result.status === 'success') {
            // Xử lý Tài liệu tham khảo (nếu có từ Lãnh đạo giao việc)
            const tkSection = document.getElementById(`${prefix}-thamKhaoSection`);
            const tkLink = document.getElementById(`${prefix}-tkLink`);
            if (tkSection) {
                if (result.data.TaiLieuThamKhaoUrl) {
                    tkSection.style.display = 'block';
                    if (tkLink) {
                        tkLink.href = result.data.TaiLieuThamKhaoUrl;
                        const tkFullName = result.data.TaiLieuThamKhaoName || 'Tài liệu tham khảo';
                        tkLink.innerText = tkFullName.split('/').pop();
                    }
                } else {
                    tkSection.style.display = 'none';
                }
            }

            // Xử lý Tài liệu đính kèm văn bản
            if (result.data.TepDinhKemUrl && fileCard) {
                fileCard.style.display = 'block';
                const link = document.getElementById(`${prefix}-fileLink`);
                if (link) {
                    link.href = result.data.TepDinhKemUrl;
                    const fullName = result.data.TepDinhKemName || 'Tài liệu đính kèm';
                    const fileName = fullName.split('/').pop();
                    link.innerText = fileName;
                }
            } else if (noFile) {
                noFile.style.display = 'block';
            }

            // Xử lý riêng cho modal Ý kiến chỉ đạo & Quyết định (modalBaoCao)
            if (prefix === 'rep') {
                const xykCard = document.getElementById('rep-xykCard');
                const groupNguoiNhan = document.getElementById('rep-group-nguoiNhan');
                const repNguoiNhan = document.getElementById('rep-nguoiNhan');
                const actionLabel = document.getElementById('rep-action-label');
                const modalTitle = document.getElementById('rep-modal-title-text');
                const submitBtn = document.getElementById('rep-submit-btn');
                const optChuyen = document.getElementById('opt-chuyen-giam-doc');
                const txtChiDao = document.getElementById('rep-noiDungChiDao');

                if (optChuyen) {
                    // Trưởng phòng có thêm lựa chọn chuyển tiếp lên Ban Giám đốc
                    optChuyen.style.display = result.data.is_truong_phong ? 'block' : 'none';
                }

                // Tự động gán mặc định Người nhận là người gửi/người xin ý kiến chỉ đạo
                if (repNguoiNhan && result.data.default_recipient_id) {
                    let opt = repNguoiNhan.querySelector(`option[value="${result.data.default_recipient_id}"]`);
                    if (!opt && result.data.default_recipient_name) {
                        opt = document.createElement('option');
                        opt.value = result.data.default_recipient_id;
                        opt.textContent = result.data.default_recipient_name;
                        repNguoiNhan.appendChild(opt);
                    }
                    repNguoiNhan.value = result.data.default_recipient_id;
                }

                if (result.data.is_xin_y_kien && result.data.xin_y_kien) {
                    const xyk = result.data.xin_y_kien;
                    if (xykCard) xykCard.style.display = 'block';
                    const sSender = document.getElementById('rep-xykSender');
                    const sRole = document.getElementById('rep-xykRole');
                    const sDept = document.getElementById('rep-xykDept');
                    const sReason = document.getElementById('rep-xykReason');
                    const sDate = document.getElementById('rep-xykDate');
                    const repIdInput = document.getElementById('rep-reportId');

                    if (sSender) sSender.textContent = xyk.nguoi_gui;
                    if (sRole) sRole.textContent = xyk.role_nguoi_gui;
                    if (sDept) sDept.textContent = xyk.phong_ban;
                    if (sReason) sReason.textContent = xyk.ly_do;
                    if (sDate) sDate.textContent = xyk.ngay_gui;
                    if (repIdInput) repIdInput.value = xyk.report_id;

                    if (groupNguoiNhan) groupNguoiNhan.style.display = 'block';
                    if (modalTitle) modalTitle.innerHTML = '<i class="fas fa-gavel"></i> Ý kiến chỉ đạo & Quyết định xử lý văn bản';
                    if (actionLabel) actionLabel.innerHTML = '<i class="fas fa-tasks" style="color:#7c3aed;"></i> Quyết định / Hướng xử lý (<span class="required">*</span>):';
                    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-gavel"></i> Ban hành quyết định & Chỉ đạo';
                    if (txtChiDao) txtChiDao.placeholder = 'Nhập ý kiến chỉ đạo, căn cứ xử lý hoặc giao nhiệm vụ cụ thể cho nhân viên...';
                } else {
                    if (xykCard) xykCard.style.display = 'none';
                    const repIdInput = document.getElementById('rep-reportId');
                    if (repIdInput) repIdInput.value = '';
                    if (groupNguoiNhan) groupNguoiNhan.style.display = 'block';
                    if (modalTitle) modalTitle.innerHTML = '<i class="fas fa-gavel"></i> Ý kiến chỉ đạo & Quyết định xử lý văn bản';
                    if (actionLabel) actionLabel.innerHTML = '<i class="fas fa-tasks" style="color:#7c3aed;"></i> Quyết định / Hướng xử lý (<span class="required">*</span>):';
                    if (submitBtn) submitBtn.innerHTML = '<i class="fas fa-gavel"></i> Ban hành quyết định & Chỉ đạo';
                    if (txtChiDao) txtChiDao.placeholder = 'Nhập ý kiến chỉ đạo, quyết định xử lý hoặc nội dung báo cáo...';
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
        const response = await fetch('/api/nguoi-dung/list/?page_size=all&exclude_admin=1');
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
    const elChiDao = document.getElementById('rep-noiDungChiDao');
    const elRepId = document.getElementById('rep-reportId');
    if (elSo) elSo.value = soKyHieu;
    if (elType) elType.value = docType;
    if (elChiDao) elChiDao.value = '';
    if (elRepId) elRepId.value = '';

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

    // AUTO-07: Gợi ý phân công tự động từ AI
    const aiSugBox = document.getElementById('asn-aiSuggestion');
    if (aiSugBox) {
        aiSugBox.style.display = 'block';
        const elLinhVuc = document.getElementById('asn-aiLinhVuc');
        const elLyDo = document.getElementById('asn-aiLyDo');
        const elNguoi = document.getElementById('asn-aiNguoiGoiY');
        if (elLinhVuc) elLinhVuc.textContent = 'Đang phân tích...';
        if (elLyDo) elLyDo.textContent = '';
        if (elNguoi) elNguoi.textContent = '';
        _aiSuggestedUserId = null;

        fetch('/api/ai/suggest-assignment/?doc_id=' + docId + '&doc_type=' + docType + '&trich_yeu=' + encodeURIComponent(trichYeu || ''))
            .then(r => r.json())
            .then(res => {
                if (res.status === 'success' && res.data) {
                    const d = res.data;
                    if (elLinhVuc) elLinhVuc.textContent = d.linh_vuc || 'Hành chính';
                    if (elLyDo) elLyDo.textContent = d.ly_do + ' Gợi ý: ';
                    if (elNguoi) elNguoi.textContent = d.user_name + ' (' + d.phong_ban_ten + ')';
                    _aiSuggestedUserId = d.user_id;
                }
            })
            .catch(err => {
                console.error('Lỗi lấy gợi ý AI:', err);
                if (aiSugBox) aiSugBox.style.display = 'none';
            });
    }

    openModal(modalId);
}

let _aiSuggestedUserId = null;

function apDungGoiYPhanCongAI() {
    if (!_aiSuggestedUserId) {
        alert("Chưa có thông tin nhân sự gợi ý từ AI!");
        return;
    }
    const uidStr = String(_aiSuggestedUserId);
    const uidNum = Number(_aiSuggestedUserId);

    if (choicesInstances['asn-nguoiXuLy']) {
        try {
            choicesInstances['asn-nguoiXuLy'].setChoiceByValue(uidStr);
        } catch (e) {
            try { choicesInstances['asn-nguoiXuLy'].setChoiceByValue(uidNum); } catch (e2) {}
        }
    }
    const select = document.getElementById('asn-nguoiXuLy');
    if (select) {
        for (let i = 0; i < select.options.length; i++) {
            if (String(select.options[i].value) === uidStr) {
                select.options[i].selected = true;
                break;
            }
        }
    }
    if (window.App && App.showSuccess) {
        App.showSuccess("Đã chọn nhân sự gợi ý từ AI!");
    }
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
            App.showAlert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
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
            App.showAlert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
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
        const action = document.getElementById('rep-actionSelect') ? document.getElementById('rep-actionSelect').value : 'DONG_Y';
        const noiDungChiDao = (document.getElementById('rep-noiDungChiDao') ? document.getElementById('rep-noiDungChiDao').value : '').trim();
        const docType = document.getElementById('rep-docType').value;
        const reportId = document.getElementById('rep-reportId') ? document.getElementById('rep-reportId').value : '';
        const recipientId = document.getElementById('rep-nguoiNhan') ? document.getElementById('rep-nguoiNhan').value : '';
        const fileInput = document.getElementById('rep-file');

        if (reportId) {
            // Trường hợp: Ban hành Quyết định / Chỉ đạo cho văn bản được xin ý kiến
            if (!noiDungChiDao) {
                App.showAlert('Vui lòng nhập nội dung ý kiến chỉ đạo & quyết định xử lý!');
                return;
            }
            formData.append('so_ky_hieu', soKyHieu);
            formData.append('action', action);
            formData.append('noi_dung_chi_dao', noiDungChiDao);
            formData.append('mo_ta', noiDungChiDao);
            formData.append('doc_type', docType);
            formData.append('report_id', reportId);
        } else {
            // Trường hợp: Báo cáo văn bản không phù hợp thông thường
            if (!noiDungChiDao || !recipientId) {
                App.showAlert('Vui lòng nhập đầy đủ thông tin bắt buộc (Người nhận và Nội dung báo cáo)!');
                return;
            }
            formData.append('so_ky_hieu', soKyHieu);
            formData.append('action', action);
            formData.append('loai_van_de', action);
            formData.append('mo_ta', noiDungChiDao);
            formData.append('doc_type', docType);
            formData.append('recipient_id', recipientId);
        }

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
            App.showAlert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
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
            App.showSuccess(result.message || 'Thao tác thành công', () => location.reload());
        } else {
            App.showError('Lỗi: ' + result.message);
        }
    } catch (e) {
        console.error(e);
        App.showError('Lỗi hệ thống!');
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
            App.showSuccess(result.message || 'Thao tác thành công', () => location.reload());
        } else {
            App.showError('Lỗi: ' + result.message);
        }
    } catch (e) {
        console.error(e);
        App.showError('Lỗi hệ thống!');
    }
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
            if (!result.data || result.data.length === 0) {
                body.innerHTML = '<tr><td colspan="7" class="text-center" style="padding: 35px; color: #64748b;"><i class="fas fa-check-circle" style="color: #10b981; font-size: 26px; margin-bottom: 8px; display: block;"></i> Hiện không có văn bản nào cần xin ý kiến chỉ đạo.</td></tr>';
            } else {
                result.data.forEach((r, idx) => {
                    const fileLinkHtml = r.file_url 
                        ? `<div style="margin-top: 4px;"><a href="${r.file_url}" target="_blank" style="font-size: 11.5px; color: #2563eb; text-decoration: none; display: inline-flex; align-items: center; gap: 4px;"><i class="fas fa-paperclip"></i> ${r.file_name || 'Tệp đính kèm'}</a></div>` 
                        : '';
                    const tagType = r.is_xin_y_kien 
                        ? '<span style="background: #f3e8ff; color: #7e22ce; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 8px; border: 1px solid #d8b4fe;"><i class="fas fa-comment-dots"></i> Xin ý kiến</span>' 
                        : `<span style="background: #fef3c7; color: #b45309; font-size: 11px; font-weight: 600; padding: 2px 7px; border-radius: 8px;">${r.loai_bao_cao}</span>`;
                    
                    const senderDept = r.phong_ban_nguoi_bao_cao ? ` - ${r.phong_ban_nguoi_bao_cao}` : '';
                    const roleInfo = r.role_nguoi_bao_cao ? `${r.role_nguoi_bao_cao}${senderDept}` : '';

                    const row = `
                        <tr style="border-bottom: 1px solid #e2e8f0;">
                            <td style="text-align: center; font-weight: 600; color: #64748b;">${idx + 1}</td>
                            <td>
                                <strong style="color: #1e293b; font-size: 13.5px;">${r.so_ky_hieu}</strong>
                                <div style="margin-top: 3px;">${tagType}</div>
                            </td>
                            <td style="max-width: 230px; font-size: 13px; color: #334155; line-height: 1.4;" title="${r.trich_yeu || ''}">
                                <div style="display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${r.trich_yeu || 'Không có trích yếu'}</div>
                                ${fileLinkHtml}
                            </td>
                            <td>
                                <strong style="color: #1e293b; font-size: 13px;">${r.nguoi_bao_cao}</strong>
                                <div style="font-size: 12px; color: #64748b; margin-top: 2px;">${roleInfo}</div>
                            </td>
                            <td>
                                <div style="font-size: 13px; color: #1e293b; background: #faf5ff; padding: 8px 12px; border-radius: 6px; border-left: 3px solid #8e44ad; font-style: italic; line-height: 1.4;">
                                    ${r.ghi_chu || 'Không có lý do chi tiết'}
                                </div>
                            </td>
                            <td style="text-align: center; font-size: 12px; color: #64748b; white-space: nowrap;">${r.ngay_bao_cao}</td>
                            <td style="text-align: center;">
                                <button class="btn btn-sm" onclick="handleReportDirectly(${r.vb_id}, '${r.so_ky_hieu}', '${r.doc_type}', ${r.id}, ${r.sender_id || 'null'}, '${escapeJsString(r.nguoi_bao_cao)}')" style="background: linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%); color: white; border: none; font-weight: 600; padding: 7px 14px; border-radius: 6px; display: inline-flex; align-items: center; gap: 5px; box-shadow: 0 2px 4px rgba(124,58,237,0.3); white-space: nowrap; cursor: pointer;">
                                    <i class="fas fa-gavel"></i> Cho ý kiến
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
        console.error('Lỗi tải danh sách báo cáo:', e);
        App.showError('Không thể tải danh sách văn bản cần xin ý kiến!');
    }
}

function escapeJsString(str) {
    return (str || '').replace(/\\/g, '\\\\').replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

function handleReportDirectly(docId, soKyHieu, docType, reportId, senderId, senderName) {
    closeModal('modalDanhSachBaoCao');
    openModalB('modalBaoCao', docId, soKyHieu, docType);
    setTimeout(() => {
        if (reportId) {
            const elRepId = document.getElementById('rep-reportId');
            if (elRepId) elRepId.value = reportId;
        }
        if (senderId) {
            const repNguoiNhan = document.getElementById('rep-nguoiNhan');
            if (repNguoiNhan) {
                let opt = repNguoiNhan.querySelector(`option[value="${senderId}"]`);
                if (!opt && senderName) {
                    opt = document.createElement('option');
                    opt.value = senderId;
                    opt.textContent = senderName;
                    repNguoiNhan.appendChild(opt);
                }
                repNguoiNhan.value = senderId;
            }
        }
    }, 150);
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
        App.showAlert('Vui lòng nhập nội dung phản hồi xử lý!');
        return;
    }
    
    if (action === 'CHUYEN' && !newRecipientId) {
        App.showAlert('Vui lòng chọn người nhận mới để chuyển tiếp báo cáo!');
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
        App.showAlert('Vui lòng nhập lý do từ chối vào ô nội dung phản hồi!');
        return;
    }
    document.getElementById('xl-huongXuLy').value = 'TU_CHOI';
    confirmXuLyBaoCao();
}

// --- Logic Phê duyệt & Phát hành văn bản đi (Bổ sung từ van_ban_di.js) ---

let _pheDuyetId = null;
let _phatHanhId = null;
let _isSigning = false;
let _sigCanvas = null;
let _sigCtx = null;

function openVBD(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'flex';
}

function closeVBD(id) {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
}

function pheDuyetVanBan(id) {
    _pheDuyetId = id;

    // Reset các thành phần thông tin
    const skhEl = document.getElementById('pd_doc_sokyhieu');
    const loaiEl = document.getElementById('pd_doc_loaivb');
    const trichYeuEl = document.getElementById('pd_doc_trichyeu');
    const fileBox = document.getElementById('pd_file_container');
    const ghiChuEl = document.getElementById('pd_ghichu');

    if (skhEl) skhEl.innerText = "Đang tải...";
    if (loaiEl) loaiEl.innerText = "---";
    if (trichYeuEl) trichYeuEl.innerText = "Đang tải thông tin văn bản...";
    if (ghiChuEl) ghiChuEl.value = "";
    if (fileBox) fileBox.innerHTML = '<span style="color: #94a3b8; font-size: 12.5px; font-style: italic;"><i class="fas fa-spinner fa-spin"></i> Đang tải tệp đính kèm...</span>';

    openVBD('popupPheDuyet');
    initSignaturePad();
    clearSignature();
    resetTieuChiChecklist();

    // Gọi API chi tiết văn bản đi để lấy trích yếu và tệp đính kèm
    fetch('/api/van-ban-di/' + id + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success' && res.data) {
                const d = res.data;
                _currentDocRole = d.user_role || {};

                // Cập nhật Header & Giao diện thích ứng theo vai trò
                const modalTitle = document.getElementById('pd_modal_title');
                const roleBadge = document.getElementById('pd_modal_role_badge');
                const btnXacNhan = document.getElementById('btnXacNhanPheDuyet');
                const btnText = document.getElementById('btnXacNhanPheDuyetText');
                const btnIcon = document.getElementById('btnXacNhanPheDuyetIcon');
                const btnTem = document.getElementById('btnTaoTemKyNhay');
                const sigLabel = document.getElementById('pd_sig_label');
                const sigSublabel = document.getElementById('pd_sig_sublabel');
                const sigPlText = document.getElementById('signature-placeholder-text');
                const knInfoBox = document.getElementById('pd_ky_nhay_info_box');

                const isGiamDoc = _currentDocRole.is_giam_doc;

                // 1. Hiển thị thông tin Ký nháy nếu đã có
                if (d.da_ky_nhay && d.thong_tin_ky_nhay && knInfoBox) {
                    knInfoBox.style.display = 'block';
                    const kn = d.thong_tin_ky_nhay;
                    const elNguoi = document.getElementById('pd_kn_nguoi_ky');
                    const elChucVu = document.getElementById('pd_kn_chuc_vu');
                    const elNgay = document.getElementById('pd_kn_ngay_ky');
                    const elGhiChu = document.getElementById('pd_kn_ghi_chu');
                    const elImg = document.getElementById('pd_kn_signature_img');
                    const elBadge = document.getElementById('pd_kn_stamp_badge');

                    if (elNguoi) elNguoi.innerText = kn.nguoi_ky || 'Lãnh đạo đơn vị';
                    if (elChucVu) elChucVu.innerText = (kn.chuc_vu || '') + (kn.phong_ban ? ' - ' + kn.phong_ban : '');
                    if (elNgay) elNgay.innerText = kn.ngay_ky || '';
                    if (elGhiChu) elGhiChu.innerText = kn.ghi_chu || 'Đã kiểm tra hợp thức đủ 4 tiêu chí';

                    if (kn.chu_ky && kn.chu_ky.startsWith('data:image')) {
                        if (elImg) {
                            elImg.src = kn.chu_ky;
                            elImg.style.display = 'inline-block';
                        }
                        if (elBadge) elBadge.style.display = 'none';
                    } else {
                        if (elImg) elImg.style.display = 'none';
                        if (elBadge) elBadge.style.display = 'inline-block';
                    }

                    // Tự động tích chọn 4 tiêu chí vì Trưởng phòng đã kiểm tra hợp thức
                    chonTatCaTieuChi(true);
                } else if (knInfoBox) {
                    knInfoBox.style.display = 'none';
                }

                // 2. Phân định vai trò Trưởng phòng vs Giám đốc
                if (isGiamDoc) {
                    if (modalTitle) modalTitle.innerText = "Phê duyệt & Ký số điện tử";
                    if (roleBadge) {
                        roleBadge.innerText = "BAN GIÁM ĐỐC";
                        roleBadge.className = "status-pill pill-blue";
                    }
                    if (btnText) btnText.innerText = "Phê duyệt & Ký số";
                    if (btnIcon) btnIcon.className = "fas fa-file-signature";
                    if (btnTem) btnTem.style.display = "none";
                    if (sigLabel) sigLabel.innerText = "Chữ ký số BGĐ";
                    if (sigSublabel) sigSublabel.innerText = "Ký số điện tử chính thức";
                    if (sigPlText) sigPlText.innerText = "Ban Giám đốc ký tên vào đây";
                } else {
                    if (modalTitle) modalTitle.innerText = "Tổng hợp & Trình duyệt văn bản lên Ban Giám đốc";
                    if (roleBadge) {
                        roleBadge.innerText = "TRƯỞNG PHÒNG TỔNG HỢP & TRÌNH DUYỆT";
                        roleBadge.className = "status-pill pill-orange";
                    }
                    if (btnText) btnText.innerText = "Tổng hợp & Trình Giám đốc";
                    if (btnIcon) btnIcon.className = "fas fa-paper-plane";
                    if (btnTem) btnTem.style.display = "inline-flex";
                    if (sigLabel) sigLabel.innerText = "Ký nháy / Xác nhận";
                    if (sigSublabel) sigSublabel.innerText = "Kiểm tra 4 tiêu chí & Ký nháy trình duyệt";
                    if (sigPlText) sigPlText.innerText = "Ký nháy hoặc bấm Đóng tem ký nháy";
                }

                if (skhEl) skhEl.innerText = d.so_ky_hieu || 'Chưa có số';
                if (loaiEl) loaiEl.innerText = d.loai_vb || 'Văn bản đi';
                if (trichYeuEl) trichYeuEl.innerText = d.trich_yeu || 'Không có trích yếu';

                if (fileBox) {
                    const fileUrl = d.tep_dinh_kem_url;
                    const fileName = d.tep_dinh_kem_name || (d.tep_dinh_kem ? d.tep_dinh_kem.split('/').pop() : '');

                    if (fileUrl && d.file_exists !== false) {
                        const ext = fileName.split('.').pop().toLowerCase();
                        const isImage = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(ext);
                        const isPdf = ext === 'pdf';

                        let html = `
                            <div style="display: flex; align-items: center; justify-content: space-between; background: #fff; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 12px; margin-top: 6px;">
                                <div style="display: flex; align-items: center; gap: 10px; overflow: hidden;">
                                    <div style="width: 34px; height: 34px; border-radius: 4px; background: ${isImage ? '#fef3c7' : (isPdf ? '#fee2e2' : '#e0f2fe')}; color: ${isImage ? '#d97706' : (isPdf ? '#dc2626' : '#0284c7')}; display: flex; align-items: center; justify-content: center; font-size: 14px; flex-shrink: 0;">
                                        <i class="${isImage ? 'fas fa-image' : (isPdf ? 'fas fa-file-pdf' : 'fas fa-file-alt')}"></i>
                                    </div>
                                    <div style="overflow: hidden;">
                                        <div style="font-weight: 600; font-size: 13px; color: #1e293b; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 320px;" title="${fileName}">
                                            ${fileName}
                                        </div>
                                        <div style="font-size: 11px; color: #64748b;">Định dạng: .${ext.toUpperCase()}</div>
                                    </div>
                                </div>
                                <div style="display: flex; gap: 8px; flex-shrink: 0;">
                                    ${isImage ? `
                                        <button type="button" class="btn btn-primary" style="padding: 5px 12px; font-size: 12px; display: inline-flex; align-items: center; gap: 5px; cursor: pointer;" onclick="openImagePreview('${fileUrl}', '${fileName}')">
                                            <i class="fas fa-eye"></i> Xem ảnh
                                        </button>
                                    ` : ''}
                                    <a href="${fileUrl}" target="_blank" class="btn btn-secondary" style="padding: 5px 12px; font-size: 12px; text-decoration: none; display: inline-flex; align-items: center; gap: 5px;">
                                        <i class="fas fa-external-link-alt"></i> ${isPdf ? 'Xem PDF' : 'Tải / Mở tệp'}
                                    </a>
                                </div>
                            </div>
                        `;

                        // Nếu là file hình ảnh, hiển thị thêm thumbnail thu nhỏ để bấm vào phóng to
                        if (isImage) {
                            html += `
                                <div style="margin-top: 10px; text-align: center; background: #f8fafc; padding: 10px; border-radius: 6px; border: 1px dashed #cbd5e1;">
                                    <div style="font-size: 12px; color: #64748b; margin-bottom: 6px;"><i class="fas fa-search-plus"></i> Bấm vào ảnh dưới đây để phóng to xem chi tiết:</div>
                                    <img src="${fileUrl}" style="max-height: 150px; max-width: 100%; object-fit: contain; border-radius: 4px; cursor: pointer; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);" onclick="openImagePreview('${fileUrl}', '${fileName}')" title="Bấm để phóng to hình ảnh">
                                </div>
                            `;
                        }

                        fileBox.innerHTML = html;
                    } else if (fileUrl && d.file_exists === false) {
                        fileBox.innerHTML = `
                            <div style="background: #fffbeb; border: 1px solid #fde68a; border-radius: 6px; padding: 10px 14px; margin-top: 6px; color: #92400e; font-size: 13px;">
                                <div style="font-weight: 600; display: flex; align-items: center; gap: 6px;"><i class="fas fa-exclamation-triangle" style="color: #f59e0b;"></i> Tệp đính kèm: ${fileName}</div>
                                <div style="font-size: 12px; color: #b45309; margin-top: 4px;">Tệp đã được ghi nhận trong cơ sở dữ liệu nhưng chưa có file vật lý trên máy chủ nội bộ.</div>
                            </div>
                        `;
                    } else {
                        fileBox.innerHTML = '<span style="color: #94a3b8; font-size: 12.5px; font-style: italic;"><i class="fas fa-info-circle"></i> Văn bản này không có tệp đính kèm.</span>';
                    }
                }
            }
        })
        .catch(err => {
            if (fileBox) fileBox.innerHTML = '<span style="color: #dc2626; font-size: 12px;">Không thể tải thông tin tệp: ' + err + '</span>';
        });
}

function openImagePreview(url, name) {
    const modal = document.getElementById('imagePreviewModal');
    const img = document.getElementById('imgPreviewSrc');
    const title = document.getElementById('imgPreviewTitle');
    const link = document.getElementById('imgPreviewNewTab');
    if (modal && img) {
        img.src = url;
        if (title) title.innerText = name || "Xem hình ảnh văn bản";
        if (link) link.href = url;
        modal.style.display = 'flex';
    }
}

function closeImagePreview() {
    const modal = document.getElementById('imagePreviewModal');
    if (modal) modal.style.display = 'none';
}

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



let _currentDocRole = {};

function taoTemKyNhay() {
    if (!_sigCanvas || !_sigCtx) return;
    const w = _sigCanvas.width;
    const h = _sigCanvas.height;

    // Clear canvas
    _sigCtx.clearRect(0, 0, w, h);

    // Background subtle tint
    _sigCtx.fillStyle = "#f8fafc";
    _sigCtx.fillRect(10, 10, w - 20, h - 20);

    // Outer double border
    _sigCtx.strokeStyle = "#1d4ed8";
    _sigCtx.lineWidth = 2;
    _sigCtx.strokeRect(10, 10, w - 20, h - 20);

    // Inner dashed line
    _sigCtx.save();
    _sigCtx.setLineDash([4, 3]);
    _sigCtx.strokeStyle = "#60a5fa";
    _sigCtx.lineWidth = 1;
    _sigCtx.strokeRect(14, 14, w - 28, h - 28);
    _sigCtx.restore();

    // Texts
    _sigCtx.fillStyle = "#1e3a8a";
    _sigCtx.textAlign = "center";
    _sigCtx.textBaseline = "middle";

    _sigCtx.font = "bold 13px 'Segoe UI', Arial, sans-serif";
    _sigCtx.fillText("✓ ĐÃ KIỂM TRA HỢP THỨC (NĐ 30/2020)", w / 2, 35);

    let roleName = (_currentDocRole && _currentDocRole.role_name) ? _currentDocRole.role_name.toUpperCase() : "LÃNH ĐẠO ĐƠN VỊ";
    let userName = (_currentDocRole && _currentDocRole.user_name) ? _currentDocRole.user_name : "Ký nháy";
    let pbName = (_currentDocRole && _currentDocRole.phong_ban) ? (" - " + _currentDocRole.phong_ban) : "";

    _sigCtx.font = "bold 12px 'Segoe UI', Arial, sans-serif";
    _sigCtx.fillStyle = "#0284c7";
    _sigCtx.fillText(roleName + pbName, w / 2, 65);

    _sigCtx.font = "italic 12px 'Segoe UI', Arial, sans-serif";
    _sigCtx.fillStyle = "#334155";
    _sigCtx.fillText("Họ tên: " + userName, w / 2, 90);

    let nowStr = new Date().toLocaleDateString('vi-VN');
    _sigCtx.font = "11px 'Segoe UI', Arial, sans-serif";
    _sigCtx.fillStyle = "#64748b";
    _sigCtx.fillText("Ngày ký nháy: " + nowStr, w / 2, 115);

    // Hide placeholder
    const placeholder = document.getElementById('signature-placeholder');
    if (placeholder) placeholder.style.display = 'none';
}

// --- BẢNG KIỂM TRA HỢP THỨC HỒ SƠ VĂN BẢN (4 TIÊU CHÍ THEO BPMN) ---
function resetTieuChiChecklist() {
    const chkNoiDung = document.getElementById('pd_chk_noi_dung');
    const chkCanCu = document.getElementById('pd_chk_can_cu');
    const chkKhaThi = document.getElementById('pd_chk_kha_thi');
    const chkHoSo = document.getElementById('pd_chk_ho_so');
    if (chkNoiDung) chkNoiDung.checked = false;
    if (chkCanCu) chkCanCu.checked = false;
    if (chkKhaThi) chkKhaThi.checked = false;
    if (chkHoSo) chkHoSo.checked = false;
    capNhatTrangThaiTieuChi();
}

function chonTatCaTieuChi(val) {
    const chkNoiDung = document.getElementById('pd_chk_noi_dung');
    const chkCanCu = document.getElementById('pd_chk_can_cu');
    const chkKhaThi = document.getElementById('pd_chk_kha_thi');
    const chkHoSo = document.getElementById('pd_chk_ho_so');
    if (chkNoiDung) chkNoiDung.checked = !!val;
    if (chkCanCu) chkCanCu.checked = !!val;
    if (chkKhaThi) chkKhaThi.checked = !!val;
    if (chkHoSo) chkHoSo.checked = !!val;
    capNhatTrangThaiTieuChi();
}

function capNhatTrangThaiTieuChi() {
    const chkNoiDung = document.getElementById('pd_chk_noi_dung');
    const chkCanCu = document.getElementById('pd_chk_can_cu');
    const chkKhaThi = document.getElementById('pd_chk_kha_thi');
    const chkHoSo = document.getElementById('pd_chk_ho_so');

    let count = 0;
    if (chkNoiDung && chkNoiDung.checked) count++;
    if (chkCanCu && chkCanCu.checked) count++;
    if (chkKhaThi && chkKhaThi.checked) count++;
    if (chkHoSo && chkHoSo.checked) count++;

    const statusBox = document.getElementById('pd_tieu_chi_status_box');
    const icon = document.getElementById('pd_tieu_chi_icon');
    const msg = document.getElementById('pd_tieu_chi_msg');
    const badge = document.getElementById('pd_tieu_chi_badge');

    if (badge) badge.innerText = count + '/4 tiêu chí';

    if (statusBox) {
        if (count === 4) {
            statusBox.style.background = '#ecfdf5';
            statusBox.style.borderColor = '#a7f3d0';
            statusBox.style.color = '#065f46';
            if (icon) icon.className = 'fas fa-check-circle';
            if (msg) msg.innerText = '✅ Hồ sơ đạt đủ 4/4 tiêu chí thẩm định (Nội dung, Căn cứ pháp lý, Tính khả thi, Hồ sơ hoàn thiện). Sẵn sàng xác nhận.';
        } else {
            statusBox.style.background = '#fffbeb';
            statusBox.style.borderColor = '#fde68a';
            statusBox.style.color = '#b45309';
            if (icon) icon.className = 'fas fa-exclamation-triangle';
            if (msg) msg.innerText = count === 0
                ? 'Chưa xác nhận tiêu chí thẩm định nào (0/4). Vui lòng rà soát dự thảo và tích chọn.'
                : 'Dự thảo chưa đạt đủ 4 tiêu chí (' + count + '/4). Nếu cần sửa đổi, hãy chọn "Yêu cầu chỉnh sửa".';
        }
    }
}

function xacNhanPheDuyet(action) {
    if (!_pheDuyetId) return;

    if (action === true) action = 'dong_y';
    if (action === false) action = 'tu_choi';

    let ghiChuEl = document.getElementById('pd_ghichu');
    let ghiChu = ghiChuEl ? ghiChuEl.value.trim() : '';

    const chkNoiDung = document.getElementById('pd_chk_noi_dung');
    const chkCanCu = document.getElementById('pd_chk_can_cu');
    const chkKhaThi = document.getElementById('pd_chk_kha_thi');
    const chkHoSo = document.getElementById('pd_chk_ho_so');

    let countTieuChi = 0;
    if (chkNoiDung && chkNoiDung.checked) countTieuChi++;
    if (chkCanCu && chkCanCu.checked) countTieuChi++;
    if (chkKhaThi && chkKhaThi.checked) countTieuChi++;
    if (chkHoSo && chkHoSo.checked) countTieuChi++;

    let chuKy = _sigCanvas ? _sigCanvas.toDataURL() : '';
    let isEmpty = true;
    if (_sigCanvas) {
        let blank = document.createElement('canvas');
        blank.width = _sigCanvas.width;
        blank.height = _sigCanvas.height;
        if (_sigCanvas.toDataURL() !== blank.toDataURL()) isEmpty = false;
    }

    let effectiveAction = action;
    if (action === 'dong_y') {
        const isGiamDoc = _currentDocRole && _currentDocRole.is_giam_doc;
        if (!isGiamDoc) {
            effectiveAction = 'ky_nhay';
        }
    }

    if (effectiveAction === 'dong_y' || effectiveAction === 'ky_nhay') {
        if (countTieuChi < 4) {
            App.showAlert("Dự thảo chưa đạt đủ 4 tiêu chí thẩm định (Nội dung chuyên môn, Căn cứ pháp lý & quy chế, Tính khả thi vận hành, Hồ sơ hoàn thiện). Vui lòng rà soát và tích xác nhận đầy đủ 4 tiêu chí trước khi " + (effectiveAction === 'ky_nhay' ? "ký nháy trình duyệt." : "phê duyệt."));
            return;
        }
        if (isEmpty) {
            App.showAlert("Vui lòng ký tên hoặc đóng tem ký nháy trước khi xác nhận.");
            return;
        }
    } else if (action === 'yeu_cau_chinh_sua') {
        let unchecked = [];
        if (chkNoiDung && !chkNoiDung.checked) unchecked.push("1. Nội dung văn bản hoặc số liệu chuyên môn chưa chính xác, chưa đạt yêu cầu");
        if (chkCanCu && !chkCanCu.checked) unchecked.push("2. Căn cứ pháp lý hoặc quy định nội bộ công ty chưa phù hợp");
        if (chkKhaThi && !chkKhaThi.checked) unchecked.push("3. Phương án chưa đảm bảo tính khả thi, nhân lực hoặc chi phí thực thi");
        if (chkHoSo && !chkHoSo.checked) unchecked.push("4. Hồ sơ dự thảo chưa tiếp thu đầy đủ chỉ đạo hoặc thiếu tài liệu căn cứ");

        if (unchecked.length > 0 && !ghiChu) {
            let templateGhiChu = "Yêu cầu chỉnh sửa các tiêu chí chưa đạt:\n- " + unchecked.join("\n- ");
            if (ghiChuEl) {
                ghiChuEl.value = templateGhiChu;
                ghiChuEl.focus();
            }
            App.showAlert("Hệ thống đã tự động điền " + unchecked.length + " tiêu chí chưa đạt vào ô Ghi chú. Vui lòng kiểm tra hoặc bổ sung thêm hướng dẫn rồi bấm lại 'Yêu cầu chỉnh sửa'.");
            return;
        }

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
        action: effectiveAction,
        chap_nhan: (effectiveAction === 'dong_y' || effectiveAction === 'ky_nhay'),
        ghi_chu: ghiChu,
        chu_ky_so: (action === 'dong_y' && !isEmpty) ? chuKy : '',
        tieu_chi: {
            noi_dung: chkNoiDung ? chkNoiDung.checked : false,
            can_cu: chkCanCu ? chkCanCu.checked : false,
            kha_thi: chkKhaThi ? chkKhaThi.checked : false,
            ho_so: chkHoSo ? chkHoSo.checked : false,
            so_luong_dat: countTieuChi
        }
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
            let defaultSuccess = (effectiveAction === 'ky_nhay') 
                ? 'Đã ký nháy văn bản và chuyển trình Ban Giám đốc thành công!'
                : (effectiveAction === 'dong_y' ? 'Phê duyệt văn bản thành công!' : 'Đã gửi phản hồi thành công!');
            let successMsg = res.message || defaultSuccess;
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


// --- BẢNG KIỂM TRA ĐIỀU KIỆN PHÁT HÀNH (4 TIÊU CHÍ BPMN) ---
function resetTieuChiPhatHanh() {
    const chkChuKy = document.getElementById('ph_chk_chu_ky');
    const chkPhuLuc = document.getElementById('ph_chk_phu_luc');
    const chkTheThuc = document.getElementById('ph_chk_the_thuc');
    const chkBenNhan = document.getElementById('ph_chk_ben_nhan');
    if (chkChuKy) chkChuKy.checked = false;
    if (chkPhuLuc) chkPhuLuc.checked = false;
    if (chkTheThuc) chkTheThuc.checked = false;
    if (chkBenNhan) chkBenNhan.checked = false;
    capNhatTrangThaiPhatHanh();
}

function chonTatCaTieuChiPhatHanh(val) {
    const chkChuKy = document.getElementById('ph_chk_chu_ky');
    const chkPhuLuc = document.getElementById('ph_chk_phu_luc');
    const chkTheThuc = document.getElementById('ph_chk_the_thuc');
    const chkBenNhan = document.getElementById('ph_chk_ben_nhan');
    if (chkChuKy) chkChuKy.checked = !!val;
    if (chkPhuLuc) chkPhuLuc.checked = !!val;
    if (chkTheThuc) chkTheThuc.checked = !!val;
    if (chkBenNhan) chkBenNhan.checked = !!val;
    capNhatTrangThaiPhatHanh();
}

function capNhatTrangThaiPhatHanh() {
    const chkChuKy = document.getElementById('ph_chk_chu_ky');
    const chkPhuLuc = document.getElementById('ph_chk_phu_luc');
    const chkTheThuc = document.getElementById('ph_chk_the_thuc');
    const chkBenNhan = document.getElementById('ph_chk_ben_nhan');

    let count = 0;
    if (chkChuKy && chkChuKy.checked) count++;
    if (chkPhuLuc && chkPhuLuc.checked) count++;
    if (chkTheThuc && chkTheThuc.checked) count++;
    if (chkBenNhan && chkBenNhan.checked) count++;

    const statusBox = document.getElementById('ph_tieu_chi_status_box');
    const icon = document.getElementById('ph_tieu_chi_icon');
    const msg = document.getElementById('ph_tieu_chi_msg');
    const badge = document.getElementById('ph_tieu_chi_badge');

    if (badge) badge.innerText = count + '/4 điều kiện';

    if (statusBox) {
        if (count === 4) {
            statusBox.style.background = '#ecfdf5';
            statusBox.style.borderColor = '#a7f3d0';
            statusBox.style.color = '#065f46';
            if (icon) icon.className = 'fas fa-check-circle';
            if (msg) msg.innerText = '✅ Đủ 4/4 điều kiện phát hành theo quy định văn thư. Sẵn sàng phát hành văn bản.';
        } else {
            statusBox.style.background = '#fffbeb';
            statusBox.style.borderColor = '#fde68a';
            statusBox.style.color = '#b45309';
            if (icon) icon.className = 'fas fa-exclamation-triangle';
            if (msg) msg.innerText = count === 0
                ? 'Chưa xác nhận đủ 4 điều kiện phát hành. Vui lòng kiểm tra và tích chọn.'
                : 'Chưa đủ 4 điều kiện phát hành (' + count + '/4). Nếu thiếu thông tin văn thư, chọn "Bổ sung / Cập nhật hồ sơ".';
        }
    }
}

function boSungCapNhatHoSoPhatHanh() {
    if (!_phatHanhId) return;
    closeVBD('popupPhatHanh');
    if (typeof suaVanBan === 'function') {
        const tr = document.querySelector(`tr[data-id="${_phatHanhId}"]`);
        if (tr) {
            suaVanBan(tr);
            return;
        }
    }
    window.location.href = `/van-ban-di/?id=${_phatHanhId}&action=edit`;
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

    // Mở popup ngay lập tức để người dùng thấy phản hồi tức thì
    openVBD('popupPhatHanh');

    // Tải chi tiết văn bản đi
    fetch('/api/van-ban-di/' + _phatHanhId + '/chi-tiet/')
        .then(r => r.json())
        .then(res => {
            if (res.status === 'success' && res.data) {
                let d = res.data;
                const docSkh = document.getElementById('ph_doc_sokyhieu');
                const docTyDisplay = document.getElementById('ph_doc_trichyeu_display');
                if (docSkh) docSkh.innerText = d.so_ky_hieu || 'Chưa có số';
                if (docTyDisplay) docTyDisplay.innerText = d.trich_yeu || 'Không có trích yếu';
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

                // Nếu văn bản đã có sẵn đơn vị ngoài từ lúc tạo dự thảo
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
    
    const chkChuKy = document.getElementById('ph_chk_chu_ky');
    const chkPhuLuc = document.getElementById('ph_chk_phu_luc');
    const chkTheThuc = document.getElementById('ph_chk_the_thuc');
    const chkBenNhan = document.getElementById('ph_chk_ben_nhan');

    let countPh = 0;
    if (chkChuKy && chkChuKy.checked) countPh++;
    if (chkPhuLuc && chkPhuLuc.checked) countPh++;
    if (chkTheThuc && chkTheThuc.checked) countPh++;
    if (chkBenNhan && chkBenNhan.checked) countPh++;

    if (countPh < 4) {
        App.showAlert("Văn bản chưa đủ 4 điều kiện phát hành theo quy trình văn thư (Chữ ký số BGĐ, Cấp số sổ văn bản đi, Đóng dấu số & định dạng PDF, Nơi nhận phân phối). Vui lòng kiểm tra và tích xác nhận đầy đủ 4 điều kiện hoặc bấm 'Bổ sung / Cập nhật hồ sơ'.");
        return;
    }

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
        don_vi_ngoai_id: (scope === 'external' || scope === 'both') ? (ph_donvi_ngoai ? ph_donvi_ngoai.value : null) : null,
        tieu_chi: {
            chu_ky: chkChuKy ? chkChuKy.checked : false,
            phu_luc: chkPhuLuc ? chkPhuLuc.checked : false,
            the_thuc: chkTheThuc ? chkTheThuc.checked : false,
            ben_nhan: chkBenNhan ? chkBenNhan.checked : false,
            so_luong_dat: countPh
        }
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
