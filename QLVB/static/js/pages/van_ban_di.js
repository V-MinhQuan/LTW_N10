function openVBD(id) {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById(id).style.display = 'block';
}
function closeVBD(id) {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById(id).style.display = 'none';
}

function checkDonVi() {
    let ngoai = document.getElementById("donViNgoai");
    let bh = document.getElementById("donViBH");
    bh.disabled = (ngoai.value !== "");
    ngoai.disabled = (bh.value !== "");
}

function luuDuThao() { 
    alert('Lưu dự thảo thành công!');
    closeVBD('modalForm'); 
}
function guiPheDuyet() { 
    alert('Gửi phê duyệt thành công!');
    closeVBD('modalForm'); 
}

function xemChiTiet(btn) {
    let row = btn.closest("tr");
    let cells = row.getElementsByTagName("td");
    document.getElementById("ct_sokyhieu").value = cells[1].innerText;
    document.getElementById("ct_trichyeu").value = cells[2].innerText;
    document.getElementById("ct_donvi").value = cells[3].innerText;
    document.getElementById("ct_loaivb").value = cells[4].innerText;
    document.getElementById("ct_nguoisoan").value = cells[5].innerText;
    document.getElementById("ct_ngay").value = cells[6].innerText;
    document.getElementById("ct_trangthai").value = cells[7].innerText;
    openVBD('modalDetail');
}
