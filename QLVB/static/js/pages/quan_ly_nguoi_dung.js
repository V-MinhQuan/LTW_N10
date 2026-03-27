const modal = document.getElementById("addModal");
const overlay = document.getElementById("modalOverlay");

function openModal() {
    modal.style.display = "block";
    overlay.style.display = "block";
}

function closeModal() {
    modal.style.display = "none";
    overlay.style.display = "none";
}

function saveData() {
    alert("Lưu thông tin người dùng thành công!");
    closeModal();
}
