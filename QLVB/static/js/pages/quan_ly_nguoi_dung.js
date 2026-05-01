console.log('quan_ly_nguoi_dung.js loaded');

const modal = document.getElementById("addModal");
const overlay = document.getElementById("modalOverlay");
const deleteModal = document.getElementById("modalDeleteUser");

let currentId = null;
let currentPage = 1;
const pageSize = 5;

// Helper function to get CSRF token
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

// Fetch Roles on load
function loadRoles() {
    fetch('/api/vai-tro/list/')
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                const select = document.getElementById('userRole');
                if (select) {
                    select.innerHTML = '<option value="">--- Chọn chức vụ ---</option>';
                    res.data.forEach(role => {
                        const opt = document.createElement('option');
                        opt.value = role.id;
                        opt.innerText = role.name;
                        select.appendChild(opt);
                    });
                }
            }
        });
}

function openModal(title, mode) {
    if (!modal) return;
    modal.style.display = "block";
    overlay.style.display = "block";
    document.getElementById('userModalTitle').innerText = title;

    const inputs = modal.querySelectorAll('.modal-input');
    const saveBtn = document.getElementById('btnSaveUser');
    const statusBtn = document.getElementById('btnUpdateStatus');
    if (mode === 'view') {
        inputs.forEach(i => i.disabled = true);
        if (saveBtn) saveBtn.style.display = 'none';
        if (statusBtn) statusBtn.style.display = 'none';
        
        const pwdGroup = document.getElementById('passwordGroup');
        if (pwdGroup) pwdGroup.style.display = 'none';
    } else if (mode === 'edit') {
        inputs.forEach(i => i.disabled = false);
        if (saveBtn) saveBtn.style.display = 'block';

        const statusInput = document.getElementById('userStatus');
        if (statusInput) statusInput.disabled = false;

        // Hiện ô mật khẩu trong Edit mode
        const pwdGroup = document.getElementById('passwordGroup');
        if (pwdGroup) pwdGroup.style.display = 'flex';
        const pwdInput = document.getElementById('userPassword');
        if (pwdInput) {
            pwdInput.value = ''; // Để trống khi edit, chỉ nhập nếu muốn đổi
            pwdInput.disabled = false;
        }

        // Chỉ hiện nút Vô hiệu hóa nếu user đang ACTIVE
        const currentStatus = (document.getElementById('userStatus').value || '').toString().toUpperCase();
        if (statusBtn) {
            statusBtn.style.display = (currentStatus === 'ACTIVE' || currentStatus === 'ĐANG HOẠT ĐỘNG') ? 'block' : 'none';
        }
    } else {
        // Add mode
        inputs.forEach(i => i.disabled = false);
        inputs.forEach(i => i.value = '');
        if (saveBtn) saveBtn.style.display = 'block';
        if (statusBtn) statusBtn.style.display = 'none';
        
        const pwdGroup = document.getElementById('passwordGroup');
        if (pwdGroup) pwdGroup.style.display = 'flex';
        const pwdInput = document.getElementById('userPassword');
        if (pwdInput) {
            pwdInput.value = '';
            pwdInput.disabled = false;
        }

        const statusInput = document.getElementById('userStatus');
        if (statusInput) {
            statusInput.value = 'ACTIVE';
            statusInput.disabled = true; // Không cho chọn khi thêm mới
        }
    }
}

window.closeModal = function () {
    if (modal) modal.style.display = "none";
    if (overlay) overlay.style.display = "none";
}

window.loadUsers = function (page = 1) {
    currentPage = page;
    const username = document.getElementById('searchUsername')?.value || '';
    const fullname = document.getElementById('searchFullName')?.value || '';
    const dept = document.getElementById('searchDept')?.value || '';
    const status = document.getElementById('searchStatus')?.value || '';

    const url = `/api/nguoi-dung/list/?page=${page}&username=${encodeURIComponent(username)}&fullname=${encodeURIComponent(fullname)}&dept=${encodeURIComponent(dept)}&status=${encodeURIComponent(status)}`;

    fetch(url)
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                renderTable(res.data, res.pagination);
                renderPagination(res.pagination);
                const headerTotal = document.querySelector('.panel-header .total-count');
                if (headerTotal) headerTotal.innerText = `Tổng số: ${res.pagination.total_count} người dùng`;
                
                const footerTotal = document.getElementById('tableTotal');
                if (footerTotal) {
                    const start = (res.pagination.current_page - 1) * pageSize + 1;
                    const end = Math.min(res.pagination.current_page * pageSize, res.pagination.total_count);
                    footerTotal.innerText = `Hiển thị ${res.pagination.total_count > 0 ? start : 0} - ${end} / Tổng số: ${res.pagination.total_count} người dùng`;
                }
            }
        })
        .catch(err => console.error('Error loading users:', err));
}

function renderTable(users, pagination) {
    const tbody = document.getElementById('userTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (users.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center;">Không tìm thấy kết quả nào</td></tr>';
        return;
    }

    const startSTT = (pagination.current_page - 1) * pageSize + 1;

    users.forEach((user, index) => {
        const tr = document.createElement('tr');

        const s_code = (user.status || '').toString().toUpperCase().trim();
        const s_label = (user.status_label || '').toString().trim();
        const isActive = (s_code === 'ACTIVE' || s_label === 'Đang hoạt động');

        const pillClass = isActive ? 'pill-active-modern' : 'pill-inactive-modern';
        const displayLabel = isActive ? 'Đang hoạt động' : 'Vô hiệu hóa';

        // --- PHÂN QUYỀN NÚT THAO TÁC Ở ĐÂY ---

        // 1. Nút Xem: Ai cũng có quyền xem
        const viewBtn = `<button type="button" class="action-btn btn-primary" onclick="viewUserById(${user.id})" title="Xem"><i class="fas fa-eye"></i></button>`;

        // 2. Nút Sửa: Chỉ hiện nếu có quyền CAN_EDIT_USER (Trưởng phòng IT)
        const editBtn = CAN_EDIT_USER
            ? `<button type="button" class="action-btn btn-success" onclick="editUserById(${user.id})" title="Sửa"><i class="fas fa-edit"></i></button>`
            : '';

        // 3. Nút Khôi phục: Chỉ hiện nếu user đang bị khóa VÀ người đang xem là IT
        const restoreBtn = (CAN_EDIT_USER && !isActive)
            ? `<button type="button" class="action-btn btn-restore" onclick="toggleUserStatusById(${user.id}, 'ACTIVE')" title="Khôi phục"><i class="fas fa-undo"></i></button>`
            : '';

        tr.innerHTML = `
            <td class="col-stt">${user.stt || (startSTT + index)}</td>
            <td>${user.username}</td>
            <td style="text-align: left;">${user.fullname}</td>
            <td>${user.dept || ''}</td>
            <td>${user.role_name || ''}</td>
            <td>${user.email}</td>
            <td class="col-status">
                <span class="status-pill ${pillClass}">${displayLabel}</span>
            </td>
            <td class="col-actions">
                ${viewBtn}
                ${editBtn}
                ${restoreBtn}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function renderPagination(pagination) {
    const container = document.getElementById('paginationControls');
    if (!container) return;
    container.innerHTML = '';

    if (pagination.total_pages <= 1) return;

    // Luôn hiện Đầu
    container.appendChild(createPageBtn('Đầu', 1, false));
    
    // Hiện Trước nếu có
    if (pagination.current_page > 1) {
        container.appendChild(createPageBtn('Trước', pagination.current_page - 1, false));
    }

    let startPage = Math.max(1, pagination.current_page - 2);
    let endPage = Math.min(pagination.total_pages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        container.appendChild(createPageBtn(i, i, i === pagination.current_page));
    }

    // Hiện Sau nếu có
    if (pagination.current_page < pagination.total_pages) {
        container.appendChild(createPageBtn('Sau', pagination.current_page + 1, false));
    }

    // Luôn hiện Cuối
    container.appendChild(createPageBtn('Cuối', pagination.total_pages, false));
}

function createPageBtn(text, page, active = false) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `page-btn ${active ? 'active' : ''}`;
    btn.innerText = text;
    if (!active) {
        btn.onclick = () => loadUsers(page);
    }
    return btn;
}

window.viewUserById = function (id) {
    fetch(`/api/nguoi-dung/list/?id=${id}`)
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success' && res.data.length > 0) {
                populateModal(res.data[0]);
                openModal('CHI TIẾT NGƯỜI DÙNG', 'view');
            }
        });
}

window.editUserById = function (id) {
    if (!CAN_EDIT_USER) {
        window.viewUserById(id);
        return;
    }
    currentId = id;
    fetch(`/api/nguoi-dung/list/?id=${id}`)
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success' && res.data.length > 0) {
                populateModal(res.data[0]);
                openModal('CHỈNH SỬA NGƯỜI DÙNG', 'edit');
            }
        });
}

function populateModal(user) {
    document.getElementById('userUsername').value = user.username;
    document.getElementById('userFullName').value = user.fullname;
    document.getElementById('userDept').value = user.dept || '';
    document.getElementById('userRole').value = user.role_id || '';
    document.getElementById('userEmail').value = user.email;
    document.getElementById('userPhone').value = user.phone || '';
    document.getElementById('userStatus').value = user.status;
}

window.toggleUserStatus = function () {
    if (!currentId) return;
    toggleUserStatusById(currentId, 'INACTIVE');
}

window.toggleUserStatusById = function (id, newStatus) {
    const isDeactivating = (newStatus === 'INACTIVE');
    const title = isDeactivating ? 'Xác nhận vô hiệu hóa' : 'Xác nhận kích hoạt lại';
    const message = isDeactivating
        ? 'Bạn có chắc muốn vô hiệu hóa người dùng này? Người dùng sẽ không thể tiếp tục sử dụng hệ thống, nhưng dữ liệu lịch sử vẫn được giữ lại.'
        : 'Bạn có chắc muốn kích hoạt lại người dùng này để tiếp tục sử dụng hệ thống?';
    const icon = isDeactivating ? 'fa-ban' : 'fa-check-circle';
    const type = isDeactivating ? 'danger' : 'success';

    App.confirm({
        title: title,
        message: message,
        type: type,
        icon: icon,
        onConfirm: () => {
            fetch('/api/nguoi-dung/update-status/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ id: id, status: newStatus })
            })
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'success') {
                        App.showSuccess(res.message, () => {
                            window.closeModal();
                            loadUsers(currentPage);
                        });
                    } else {
                        alert('Lỗi: ' + res.message);
                    }
                });
        }
    });
}

window.saveData = function () {
    const payload = {
        id: currentId,
        username: document.getElementById('userUsername').value,
        fullname: document.getElementById('userFullName').value,
        email: document.getElementById('userEmail').value,
        phone: document.getElementById('userPhone').value,
        dept: document.getElementById('userDept').value,
        role_id: document.getElementById('userRole').value,
        status: (currentId === null) ? 'ACTIVE' : document.getElementById('userStatus').value,
        password: document.getElementById('userPassword').value
    };

    if (!payload.username || !payload.fullname || !payload.email || !payload.dept || !payload.role_id) {
        alert('Vui lòng điền đầy đủ các trường bắt buộc (*)');
        return;
    }

    if (currentId === null && !payload.password) {
        alert('Vui lòng nhập mật khẩu cho người dùng mới');
        return;
    }

    fetch('/api/nguoi-dung/upsert/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
        .then(res => res.json())
        .then(res => {
            if (res.status === 'success') {
                App.showSuccess(res.message, () => {
                    closeModal();
                    loadUsers(currentPage);
                });
            } else {
                alert('Lỗi: ' + res.message);
            }
        })
        .catch(err => {
            console.error('Save error:', err);
            alert('Đã xảy ra lỗi khi lưu.');
        });
}

document.addEventListener('DOMContentLoaded', function () {
    loadRoles();
    loadUsers(1);

    // Search button
    const searchBtn = document.querySelector('.btn-primary[onclick*="search"]'); // Adjust if needed
    // The index.html has button with i class fas fa-search
    const buttons = document.querySelectorAll('.btn-group .btn');
    buttons.forEach(btn => {
        if (btn.innerText.includes('Tìm kiếm')) {
            btn.onclick = () => loadUsers(1);
        }
        if (btn.innerText.includes('Làm mới')) {
            btn.onclick = () => {
                document.getElementById('searchUsername').value = '';
                document.getElementById('searchFullName').value = '';
                document.getElementById('searchDept').value = '';
                document.getElementById('searchStatus').value = '';
                loadUsers(1);
            };
        }
    });

    const addBtn = document.querySelector('.btn-success');
    if (addBtn) {
        addBtn.onclick = function () {
            currentId = null;
            openModal('THÊM NGƯỜI DÙNG MỚI', 'add');
        };
    }
});
