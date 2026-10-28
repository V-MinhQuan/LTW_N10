import os

with open('QLVB/static/js/pages/van_ban_den.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

# 1. Update the DOMContentLoaded listener to automatically trigger OCR and handle Drag & Drop
old_listener = """    const addFileInput = document.getElementById('popupAddFileInput');
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
    }"""

new_listener = """    const addFileInput = document.getElementById('popupAddFileInput');
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
    }"""

# 2. Update quyetDuLieuOCRVanBanDen to accept customFile and highlight inputs
old_ocr_func = """function quyetDuLieuOCRVanBanDen() {
    const fileInput = document.getElementById('popupAddFileInput');
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
        alert("Vui lòng chọn hoặc kéo thả tệp văn bản trước khi bấm Quét OCR!");
        if (fileInput) fileInput.click();
        return;
    }

    const file = fileInput.files[0];
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
        badgeText.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang đọc và nhận dạng ký tự quang học (OCR)...';
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
                if (d.trich_yeu) form.elements['trich_yeu'].value = d.trich_yeu;
                if (d.so_ky_hieu) form.elements['so_ky_hieu'].value = d.so_ky_hieu;
                if (d.loai_van_ban) form.elements['loai_van_ban'].value = d.loai_van_ban;
                if (d.ngay_ban_hanh) form.elements['ngay_ban_hanh'].value = d.ngay_ban_hanh;
                if (d.co_quan_ban_hanh) form.elements['don_vi_ngoai_id'].value = d.co_quan_ban_hanh;
            }

            if (badge) {
                badge.style.background = '#f0fdf4';
                badge.style.borderColor = '#86efac';
                badge.style.color = '#166534';
                badgeText.innerHTML = `✨ <b>AI OCR thành công:</b> Đã tự động nhận diện và điền thông tin (Số: <b>${d.so_ky_hieu || 'N/A'}</b>, Loại: <b>${d.loai_van_ban}</b>, Ban hành: <b>${d.ngay_ban_hanh}</b>)!`;
            }
            if (window.App && App.showSuccess) {
                App.showSuccess("Đã quét OCR và tự động điền các trường văn bản thành công!");
            }
        } else {
            if (badge) {
                badge.style.background = '#fef2f2';
                badge.style.borderColor = '#fca5a5';
                badge.style.color = '#991b1b';
                badgeText.innerHTML = `<i class="fas fa-exclamation-triangle"></i> ${res.message || 'Không thể quét OCR'}`;
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (badge) {
            badge.style.background = '#fef2f2';
            badge.style.borderColor = '#fca5a5';
            badge.style.color = '#991b1b';
            badgeText.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Lỗi kết nối khi quét OCR!';
        }
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    });
}"""

new_ocr_func = """function _highlightOCRField(input) {
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
}"""

js_norm = js_code.replace('\r\n', '\n')
old_listener_norm = old_listener.replace('\r\n', '\n')
new_listener_norm = new_listener.replace('\r\n', '\n')

old_ocr_norm = old_ocr_func.replace('\r\n', '\n')
new_ocr_norm = new_ocr_func.replace('\r\n', '\n')

assert old_listener_norm in js_norm, "old_listener not found"
js_norm = js_norm.replace(old_listener_norm, new_listener_norm, 1)

assert old_ocr_norm in js_norm, "old_ocr_func not found"
js_norm = js_norm.replace(old_ocr_norm, new_ocr_norm, 1)

with open('QLVB/static/js/pages/van_ban_den.js', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(js_norm)
print("SUCCESS: Updated van_ban_den.js")

