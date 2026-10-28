with open('QLVB/static/js/pages/van_ban_di.js', 'r', encoding='utf-8') as f:
    js_code = f.read()

vbd_ocr_code = """

// ==============================================================================
// GIAI ĐOẠN 3 (PHASE 3): AI OCR & TỰ ĐỘNG ĐIỀN THÔNG TIN VĂN BẢN ĐI
// ==============================================================================

function _highlightOCRFieldVBD(input) {
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

function xuLyTepDinhKemVanBanDi(inputOrFile) {
    let file = null;
    if (inputOrFile instanceof File) {
        file = inputOrFile;
    } else if (inputOrFile && inputOrFile.files && inputOrFile.files[0]) {
        file = inputOrFile.files[0];
    }

    const labelElem = document.getElementById('fileLabel');
    if (file) {
        if (labelElem) {
            labelElem.innerHTML = `
                <div style="font-weight: 600; color: #0284c7;">
                    <i class="fas fa-file-alt me-1"></i> ${file.name}
                    <span style="font-size: 12px; color: #64748b; font-weight: normal;">(${(file.size / 1024).toFixed(1)} KB)</span>
                </div>
            `;
        }
        // TỰ ĐỘNG QUÉT OCR & ĐIỀN DỮ LIỆU TỨC THÌ
        quyetDuLieuOCRVanBanDi(file);
    } else {
        if (labelElem) {
            labelElem.innerHTML = 'Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính';
        }
        const badge = document.getElementById('vbd_ocr_status_badge');
        if (badge) badge.style.display = 'none';
    }
}

function quyetDuLieuOCRVanBanDi(customFile) {
    let file = customFile;
    if (!file) {
        const fi = document.getElementById('fileInput');
        if (fi && fi.files && fi.files[0]) {
            file = fi.files[0];
        }
    }

    if (!file) {
        alert("Vui lòng chọn hoặc kéo thả tệp văn bản trước khi quét OCR!");
        const fi = document.getElementById('fileInput');
        if (fi) fi.click();
        return;
    }

    const btn = document.getElementById('btnOcrScanVBD');
    const origHtml = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang quét OCR...';
    }

    const badge = document.getElementById('vbd_ocr_status_badge');
    const badgeText = document.getElementById('vbd_ocr_status_text');
    if (badge) {
        badge.style.display = 'block';
        badge.style.background = '#eff6ff';
        badge.style.borderColor = '#93c5fd';
        badge.style.color = '#1e40af';
        if (badgeText) badgeText.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> <b>AI OCR đang quét tệp:</b> Đang trích xuất Số ký hiệu, Loại văn bản, Ngày tháng, Cơ quan ban hành...';
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

            // 1. Trích yếu
            const trichYeuEl = document.getElementById('trichYeu');
            if (trichYeuEl && d.trich_yeu) {
                trichYeuEl.value = d.trich_yeu;
                _highlightOCRFieldVBD(trichYeuEl);
            }

            // 2. Loại văn bản
            const loaiVbEl = document.getElementById('loaiVB');
            if (loaiVbEl && d.loai_van_ban) {
                for (let i = 0; i < loaiVbEl.options.length; i++) {
                    if (loaiVbEl.options[i].value.toLowerCase() === d.loai_van_ban.toLowerCase()) {
                        loaiVbEl.selectedIndex = i;
                        break;
                    }
                }
                _highlightOCRFieldVBD(loaiVbEl);
            }

            // 3. Số ký hiệu
            const soKyHieuEl = document.getElementById('soKyHieu');
            if (soKyHieuEl && d.so_ky_hieu) {
                soKyHieuEl.value = d.so_ky_hieu;
                _highlightOCRFieldVBD(soKyHieuEl);
            }

            // 4. Ngày ban hành
            const ngayEl = document.getElementById('ngayBanHanh');
            if (ngayEl && d.ngay_ban_hanh) {
                ngayEl.value = d.ngay_ban_hanh;
                _highlightOCRFieldVBD(ngayEl);
            }

            // 5. Đơn vị bên ngoài
            const dvNgoaiEl = document.getElementById('donViNgoai');
            if (dvNgoaiEl && (d.co_quan_ban_hanh || d.don_vi_ngoai_ten)) {
                dvNgoaiEl.value = d.don_vi_ngoai_ten || d.co_quan_ban_hanh;
                _highlightOCRFieldVBD(dvNgoaiEl);
            }

            if (badge) {
                badge.style.background = '#f0fdf4';
                badge.style.borderColor = '#86efac';
                badge.style.color = '#166534';
                if (badgeText) {
                    badgeText.innerHTML = `✨ <b>AI OCR thành công:</b> Đã tự động điền các trường văn bản (Loại: <b>${d.loai_van_ban}</b> | Số: <b>${d.so_ky_hieu || 'Cấp tự động'}</b> | Ngày: <b>${d.ngay_ban_hanh}</b>)!`;
                }
            }
            if (window.App && App.showSuccess) {
                App.showSuccess("AI đã quét OCR và tự động điền các ô dữ liệu thành công!");
            }
        } else {
            if (badge) {
                badge.style.background = '#fef2f2';
                badge.style.borderColor = '#fca5a5';
                badge.style.color = '#991b1b';
                if (badgeText) badgeText.innerHTML = `<i class="fas fa-exclamation-triangle me-1"></i> ${res.message || 'Không thể quét OCR nội dung văn bản này'}`;
            }
        }
    })
    .catch(err => {
        console.error(err);
        if (badge) {
            badge.style.background = '#fef2f2';
            badge.style.borderColor = '#fca5a5';
            badge.style.color = '#991b1b';
            if (badgeText) badgeText.innerHTML = '<i class="fas fa-exclamation-triangle me-1"></i> Lỗi kết nối khi quét OCR!';
        }
    })
    .finally(() => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
    });
}

// Khởi tạo kéo & thả cho modalForm Văn bản đi
document.addEventListener('DOMContentLoaded', () => {
    const uploadAreaVBD = document.getElementById('vbd_modal_upload_area');
    const fileInputVBD = document.getElementById('fileInput');

    if (uploadAreaVBD) {
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadAreaVBD.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadAreaVBD.style.borderColor = '#0284c7';
                uploadAreaVBD.style.backgroundColor = '#f0f9ff';
            }, false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadAreaVBD.addEventListener(eventName, function(e) {
                e.preventDefault();
                e.stopPropagation();
                uploadAreaVBD.style.borderColor = '';
                uploadAreaVBD.style.backgroundColor = '';
            }, false);
        });

        uploadAreaVBD.addEventListener('drop', function(e) {
            const dt = e.dataTransfer;
            if (dt && dt.files && dt.files.length > 0) {
                const file = dt.files[0];
                if (fileInputVBD) {
                    try { fileInputVBD.files = dt.files; } catch (err) {}
                }
                xuLyTepDinhKemVanBanDi(file);
            }
        }, false);
    }
});
"""

# Append vbd_ocr_code if not already present
if 'quyetDuLieuOCRVanBanDi' not in js_code:
    js_code += vbd_ocr_code
    with open('QLVB/static/js/pages/van_ban_di.js', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(js_code)
    print("SUCCESS: Added OCR auto-fill to van_ban_di.js")
else:
    print("ALREADY PRESENT: quyetDuLieuOCRVanBanDi in van_ban_di.js")

