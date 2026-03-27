function openUnitModal(title) {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('modalUnit').style.display = 'block';
    document.getElementById('unitModalTitle').innerText = title;
}

function closeUnitModal() {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById('modalUnit').style.display = 'none';
}

function viewUnit(btn) {
    const row = btn.closest('tr');
    const cells = row.getElementsByTagName('td');
    document.getElementById('unitName').value = cells[1].innerText;
    document.getElementById('unitAddress').value = cells[2].innerText;
    document.getElementById('unitPhone').value = cells[3].innerText;
    document.getElementById('unitEmail').value = cells[4].innerText;
    document.getElementById('unitContact').value = cells[5].innerText;
    
    // Disable inputs for viewing
    const inputs = document.getElementById('modalUnit').querySelectorAll('input');
    inputs.forEach(i => i.disabled = true);
    document.getElementById('btnSaveUnit').style.display = 'none';
    
    openUnitModal('Chi tiết đơn vị');
}

function editUnit(btn) {
    const row = btn.closest('tr');
    const cells = row.getElementsByTagName('td');
    document.getElementById('unitName').value = cells[1].innerText;
    document.getElementById('unitAddress').value = cells[2].innerText;
    document.getElementById('unitPhone').value = cells[3].innerText;
    document.getElementById('unitEmail').value = cells[4].innerText;
    document.getElementById('unitContact').value = cells[5].innerText;
    
    // Enable inputs for editing
    const inputs = document.getElementById('modalUnit').querySelectorAll('input');
    inputs.forEach(i => i.disabled = false);
    document.getElementById('btnSaveUnit').style.display = 'block';
    
    openUnitModal('Chỉnh sửa đơn vị');
}

function saveUnit() {
    alert('Lưu thông tin thành công!');
    closeUnitModal();
}

function confirmDelete(btn) {
    document.getElementById('modalOverlay').style.display = 'block';
    document.getElementById('modalDelete').style.display = 'block';
}

function closeDeleteModal() {
    document.getElementById('modalOverlay').style.display = 'none';
    document.getElementById('modalDelete').style.display = 'none';
}

function deleteConfirm() {
    alert('Đã xóa đơn vị!');
    closeDeleteModal();
}

// Hook up "Thêm mới" button using class/index logic
document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.querySelector('.btn-green');
    if (addBtn) {
        addBtn.onclick = function() {
            document.getElementById('unitName').value = '';
            document.getElementById('unitAddress').value = '';
            document.getElementById('unitPhone').value = '';
            document.getElementById('unitEmail').value = '';
            document.getElementById('unitContact').value = '';
            
            const inputs = document.getElementById('modalUnit').querySelectorAll('input');
            inputs.forEach(i => i.disabled = false);
            document.getElementById('btnSaveUnit').style.display = 'block';
            
            openUnitModal('Thêm mới đơn vị');
        };
    }
});
