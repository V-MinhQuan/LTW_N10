function openVBD(id) {
    let el = document.getElementById(id);
    if (el) {
        if (el.classList.contains('vbd-popup-overlay')) {
            // Move ra body để tránh bị trapped bởi overflow của parent
            if (el.parentElement !== document.body) {
                document.body.appendChild(el);
            }
            el.style.display = 'flex';
        } else {
            let overlay = document.getElementById('modalOverlay');
            if (overlay) overlay.style.display = 'block';
            el.style.display = 'block';
        }
    }
}
function closeVBD(id) {
    let el = document.getElementById(id);
    if (el) {
        el.style.display = 'none';
        if (!el.classList.contains('vbd-popup-overlay')) {
            let overlay = document.getElementById('modalOverlay');
            if (overlay) overlay.style.display = 'none';
        }
    }
}

// Close on overlay click
window.onclick = function(event) {
    if (event.target.classList.contains('vbd-popup-overlay')) {
        event.target.style.display = "none";
    }
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
