function openModal(modalId) {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById(modalId).style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById(modalId).style.display = 'none';
}

function openModalC(modalId, soKyHieu, nguoiXuLy) {
    document.getElementById('upd-soKyHieu').value = soKyHieu;
    document.getElementById('upd-nguoiXuLy').value = nguoiXuLy;
    openModal(modalId);
}

function openModalT(modalId, soKyHieu) {
    document.getElementById('fwd-soKyHieu').value = soKyHieu;
    openModal(modalId);
}

function openModalB(modalId, soKyHieu) {
    document.getElementById('rep-soKyHieu').value = soKyHieu;
    openModal(modalId);
}

function openModalP(modalId, soKyHieu, trichYeu) {
    document.getElementById('asn-soKyHieu').value = soKyHieu;
    document.getElementById('asn-trichYeu').value = trichYeu;
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
