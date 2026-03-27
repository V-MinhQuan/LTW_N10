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

function saveAndClose(modalId) {
    alert('Thao tác thành công!');
    closeModal(modalId);
}
