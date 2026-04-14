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
    openModal(modalId);
}

function openModalT(modalId, soKyHieu) {
    const el = document.getElementById('fwd-soKyHieu');
    if (el) el.value = soKyHieu;
    openModal(modalId);
}

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
    openModal(modalId);
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
            noi_dung: document.getElementById('upd-noiDung').value
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
            noi_dung: document.getElementById('fwd-noiDung').value
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
            mo_ta: document.getElementById('rep-moTa').value
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
            ghi_chu: document.getElementById('asn-ghiChu').value
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
