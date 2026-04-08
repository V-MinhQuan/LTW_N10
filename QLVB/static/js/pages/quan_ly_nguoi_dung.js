const modal = document.getElementById("addModal");
const overlay = document.getElementById("modalOverlay");
const deleteModal = document.getElementById("modalDeleteUser");

function openModal(title, mode) {
    modal.style.display = "block";
    overlay.style.display = "block";
    document.getElementById('userModalTitle').innerText = title;
    
    const inputs = modal.querySelectorAll('.modal-input');
    const saveBtn = document.getElementById('btnSaveUser');
    const passwordField = document.getElementById('passwordField');

    if (mode === 'view') {
        inputs.forEach(i => i.disabled = true);
        saveBtn.style.display = 'none';
        passwordField.style.display = 'none';
    } else if (mode === 'edit') {
        inputs.forEach(i => i.disabled = false);
        saveBtn.style.display = 'block';
        passwordField.style.display = 'none'; // Hide password during edit in this demo
    } else {
        // Add mode
        inputs.forEach(i => i.disabled = false);
        inputs.forEach(i => i.value = '');
        saveBtn.style.display = 'block';
        passwordField.style.display = 'block';
    }
}

function closeModal() {
    modal.style.display = "none";
    overlay.style.display = "none";
}

function viewUser(btn) {
    const row = btn.closest('tr');
    const cells = row.getElementsByTagName('td');
    
    document.getElementById('userUsername').value = cells[1].innerText;
    document.getElementById('userFullName').value = cells[2].innerText;
    document.getElementById('userDept').value = cells[3].innerText;
    document.getElementById('userRole').value = cells[4].innerText;
    document.getElementById('userEmail').value = cells[5].innerText;
    
    const statusText = cells[6].innerText.trim();
    document.getElementById('userStatus').value = statusText;

    openModal('CHI TIẾT NGƯỜI DÙNG', 'view');
}

function editUser(btn) {
    const row = btn.closest('tr');
    const cells = row.getElementsByTagName('td');
    
    document.getElementById('userUsername').value = cells[1].innerText;
    document.getElementById('userFullName').value = cells[2].innerText;
    document.getElementById('userDept').value = cells[3].innerText;
    document.getElementById('userRole').value = cells[4].innerText;
    document.getElementById('userEmail').value = cells[5].innerText;
    
    const statusText = cells[6].innerText.trim();
    document.getElementById('userStatus').value = statusText;

    openModal('CHỈNH SỬA NGƯỜI DÙNG', 'edit');
}

function confirmDeleteUser(btn) {
    overlay.style.display = "block";
    deleteModal.style.display = "block";
}

function closeDeleteUserModal() {
    overlay.style.display = "none";
    deleteModal.style.display = "none";
}

function deleteUserConfirm() {
    alert("Đã xóa người dùng thành công!");
    closeDeleteUserModal();
}

function saveData() {
    alert("Lưu thông tin người dùng thành công!");
    closeModal();
}

// Ensure "Thêm mới" works correctly
document.addEventListener('DOMContentLoaded', function() {
    const addBtn = document.querySelector('.btn-success[onclick="openModal()"]');
    if (addBtn) {
        addBtn.onclick = function() {
            openModal('THÊM NGƯỜI DÙNG MỚI', 'add');
        };
    }
});
