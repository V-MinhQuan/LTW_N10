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

function openModalC(modalId, soKyHieu, nguoiXuLy) {
    const elSo = document.getElementById('upd-soKyHieu');
    const elNguoi = document.getElementById('upd-nguoiXuLy');
    if (elSo) elSo.value = soKyHieu;
    if (elNguoi) elNguoi.value = nguoiXuLy;
function openModalC(modalId, soKyHieu, nguoiXuLy, docType) {
    document.getElementById('upd-soKyHieu').value = soKyHieu;
    document.getElementById('upd-nguoiXuLy').value = nguoiXuLy;
    document.getElementById('upd-docType').value = docType;
    openModal(modalId);
}

function openModalT(modalId, soKyHieu, docType) {
    document.getElementById('fwd-soKyHieu').value = soKyHieu;
    document.getElementById('fwd-docType').value = docType;
function openModalT(modalId, soKyHieu) {
    const el = document.getElementById('fwd-soKyHieu');
    if (el) el.value = soKyHieu;
    openModal(modalId);
}

function openModalB(modalId, soKyHieu, docType) {
    document.getElementById('rep-soKyHieu').value = soKyHieu;
    document.getElementById('rep-docType').value = docType;
function openModalB(modalId, soKyHieu) {
    const el = document.getElementById('rep-soKyHieu');
    if (el) el.value = soKyHieu;
    openModal(modalId);
}

function openModalP(modalId, soKyHieu, trichYeu) {
    const elSo = document.getElementById('asn-soKyHieu');
    const elTrich = document.getElementById('asn-trichYeu');
    if (elSo) elSo.value = soKyHieu;
    if (elTrich) elTrich.value = trichYeu;
function openModalP(modalId, soKyHieu, trichYeu, docType) {
    document.getElementById('asn-soKyHieu').value = soKyHieu;
    document.getElementById('asn-trichYeu').value = trichYeu;
    document.getElementById('asn-docType').value = docType;
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
            doc_type: document.getElementById('upd-docType').value
        };
        if (!data.trang_thai || !data.noi_dung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalChuyenTiep') {
        url = '/api/xu-ly-van-ban/chuyen-tiep/';
        data = {
            so_ky_hieu: document.getElementById('fwd-soKyHieu').value,
            don_vi_id: document.getElementById('fwd-nguoiNhan').value,
            noi_dung: document.getElementById('fwd-noiDung').value,
            doc_type: document.getElementById('fwd-docType').value
        };
        if (!data.don_vi_id || !data.noi_dung) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalBaoCao') {
        url = '/api/xu-ly-van-ban/bao-cao/';
        data = {
            so_ky_hieu: document.getElementById('rep-soKyHieu').value,
            loai_van_de: document.getElementById('rep-loaiVanDe').value,
            mo_ta: document.getElementById('rep-moTa').value,
            doc_type: document.getElementById('rep-docType').value
        };
        if (!data.loai_van_de || !data.mo_ta) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
            return;
        }
    } else if (modalId === 'modalPhanCong') {
        url = '/api/xu-ly-van-ban/phan-cong/';
        data = {
            so_ky_hieu: document.getElementById('asn-soKyHieu').value,
            user_id: document.getElementById('asn-nguoiXuLy').value,
            han_xu_ly: document.getElementById('asn-thoiHan').value,
            ghi_chu: document.getElementById('asn-ghiChu').value,
            doc_type: document.getElementById('asn-docType').value
        };
        if (!data.user_id || !data.han_xu_ly) {
            alert('Vui lòng nhập đầy đủ thông tin bắt buộc!');
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

document.addEventListener('DOMContentLoaded', function() {
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
    const fileNameDisplayUpd = document.getElementById('upd-fileName');
    const uploadAreaUpd = document.getElementById('uploadFileArea_upd');

    if (fileInputUpd && fileNameDisplayUpd) {
        fileInputUpd.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                fileNameDisplayUpd.textContent = 'Đã chọn tệp: ' + this.files[0].name;
            } else {
                fileNameDisplayUpd.textContent = '';
            }
        });
    }

    if (uploadAreaUpd && fileInputUpd) {
        uploadAreaUpd.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadAreaUpd.style.backgroundColor = '#e6f3ff';
        });

        uploadAreaUpd.addEventListener('dragleave', function(e) {
            e.preventDefault();
            uploadAreaUpd.style.backgroundColor = '#f8fbff';
        });

        uploadAreaUpd.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadAreaUpd.style.backgroundColor = '#f8fbff';
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                fileInputUpd.files = e.dataTransfer.files;
                fileInputUpd.dispatchEvent(new Event('change'));
            }
        });
    }
});
