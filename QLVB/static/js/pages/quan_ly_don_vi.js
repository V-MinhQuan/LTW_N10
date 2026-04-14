console.log('quan_ly_don_vi.js loaded');

let currentId = null;
let currentType = location.href.includes('ben-trong') ? 'trong' : 'ngoai';
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

window.openUnitModal = function(title) {
    console.log('Opening modal:', title);
    const overlay = document.getElementById('modalOverlay');
    const modal = document.getElementById('modalUnit');
    if (overlay && modal) {
        overlay.style.display = 'block';
        modal.style.display = 'block';
        document.getElementById('unitModalTitle').innerText = title;
    }
}

window.closeUnitModal = function() {
    const overlay = document.getElementById('modalOverlay');
    const modal = document.getElementById('modalUnit');
    if (overlay && modal) {
        overlay.style.display = 'none';
        modal.style.display = 'none';
    }
    currentId = null;
}

window.loadUnits = function(page = 1) {
    console.log('Loading units for page:', page);
    currentPage = page;
    const name = document.querySelector('input[name="name"]')?.value || '';
    const address = document.querySelector('input[name="address"]')?.value || '';
    const contact = document.querySelector('input[name="contact"]')?.value || '';

    const url = `${window.location.pathname}?page=${page}&ajax=1&name=${encodeURIComponent(name)}&address=${encodeURIComponent(address)}&contact=${encodeURIComponent(contact)}`;
    console.log('Fetch URL:', url);

    fetch(url)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(result => {
            console.log('Fetch success:', result);
            if (result.status === 'success') {
                renderTable(result.data, result.pagination);
                renderPagination(result.pagination);
                const totalElem = document.getElementById('tableTotal');
                if (totalElem) totalElem.innerText = `Tổng số: ${result.pagination.total_count}`;
            } else {
                alert('Lỗi: ' + result.message);
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            alert('Đã xảy ra lỗi khi tải dữ liệu. Vui lòng thử lại.');
        });
}

function renderTable(units, pagination) {
    const tbody = document.getElementById('unitTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';

    if (units.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center;">Không tìm thấy kết quả nào</td></tr>';
        return;
    }

    const startSTT = (pagination.current_page - 1) * pageSize + 1;

    units.forEach((unit, index) => {
        const tr = document.createElement('tr');
        tr.dataset.id = unit.id;
        tr.dataset.type = currentType;

        tr.innerHTML = `
            <td class="col-stt">${startSTT + index}</td>
            <td style="text-align: left;"><a href="javascript:void(0)" class="text-blue" onclick="viewUnitById(${unit.id})">${unit.name}</a></td>
            <td style="text-align: left;">${unit.address || ''}</td>
            <td>${unit.phone || ''}</td>
            <td>${unit.email || ''}</td>
            <td>${unit.contact || ''}</td>
            <td class="col-actions">
                <button type="button" class="action-btn btn-primary" onclick="viewUnitById(${unit.id})" title="Xem"><i class="fas fa-eye"></i></button>
                <button type="button" class="action-btn btn-success" onclick="editUnitById(${unit.id})" title="Sửa"><i class="fas fa-edit"></i></button>
                <button type="button" class="action-btn btn-danger" onclick="confirmDeleteById(${unit.id})" title="Xóa"><i class="fas fa-trash-alt"></i></button>
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

    // Ordered: Đầu - Numbers - Sau - Cuối
    container.appendChild(createPageBtn('Đầu', 1));

    let startPage = Math.max(1, pagination.current_page - 2);
    let endPage = Math.min(pagination.total_pages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        container.appendChild(createPageBtn(i, i, i === pagination.current_page));
    }

    if (pagination.has_next) {
        container.appendChild(createPageBtn('Sau', pagination.current_page + 1));
    }
    
    container.appendChild(createPageBtn('Cuối', pagination.total_pages));
}

function createPageBtn(text, page, active = false) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `page-btn ${active ? 'active' : ''}`;
    btn.innerText = text;
    if (!active) {
        btn.onclick = (e) => {
            e.preventDefault();
            loadUnits(page);
        };
    }
    return btn;
}

window.viewUnitById = function(id) {
    fetchSingleUnit(id, data => {
        populateModal(data);
        const modal = document.getElementById('modalUnit');
        const inputs = modal.querySelectorAll('input');
        inputs.forEach(i => i.disabled = true);
        const saveBtn = document.getElementById('btnSaveUnit');
        if (saveBtn) saveBtn.style.display = 'none';
        openUnitModal('Chi tiết đơn vị');
    });
};

window.editUnitById = function(id) {
    currentId = id;
    fetchSingleUnit(id, data => {
        populateModal(data);
        const modal = document.getElementById('modalUnit');
        const inputs = modal.querySelectorAll('input');
        inputs.forEach(i => i.disabled = false);
        const saveBtn = document.getElementById('btnSaveUnit');
        if (saveBtn) saveBtn.style.display = 'block';
        openUnitModal('Chỉnh sửa đơn vị');
    });
};

window.confirmDeleteById = function(id) {
    App.confirmDelete("Bạn có chắc chắn muốn xóa đơn vị này không?", function() {
        deleteConfirmById(id);
    });
};

function deleteConfirmById(id) {
    if (!id) return;
    fetch('/api/don-vi/delete/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ id: id, type: currentType })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            App.showSuccess(data.message, () => {
                loadUnits(currentPage);
            });
        } else {
            alert('Lỗi: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Đã xảy ra lỗi khi xóa.');
    });
}

// Compatible with SSR rows
window.viewUnit = function(btn) {
    const data = btn.dataset;
    populateModal({
        name: data.name,
        address: data.address,
        phone: data.phone,
        email: data.email,
        contact: data.contact
    });
    const inputs = document.getElementById('modalUnit').querySelectorAll('input');
    inputs.forEach(i => i.disabled = true);
    document.getElementById('btnSaveUnit').style.display = 'none';
    openUnitModal('Chi tiết đơn vị');
};

window.editUnit = function(btn) {
    const data = btn.dataset;
    currentId = data.id;
    populateModal({
        name: data.name,
        address: data.address,
        phone: data.phone,
        email: data.email,
        contact: data.contact
    });
    const inputs = document.getElementById('modalUnit').querySelectorAll('input');
    inputs.forEach(i => i.disabled = false);
    document.getElementById('btnSaveUnit').style.display = 'block';
    openUnitModal('Chỉnh sửa đơn vị');
};

window.confirmDelete = function(btn) {
    const id = btn.dataset.id;
    App.confirmDelete("Bạn có chắc chắn muốn xóa đơn vị này không?", function() {
        deleteConfirmById(id);
    });
};

function fetchSingleUnit(id, callback) {
    const url = `${window.location.pathname}?id=${id}&ajax=1`;
    fetch(url)
        .then(response => response.json())
        .then(result => {
             if (result.status === 'success' && result.data.length > 0) {
                 callback(result.data[0]);
             }
        })
        .catch(err => console.error('Error fetching unit:', err));
}

function populateModal(data) {
    const nameInput = document.getElementById('unitName');
    const addrInput = document.getElementById('unitAddress');
    const phoneInput = document.getElementById('unitPhone');
    const emailInput = document.getElementById('unitEmail');
    const contactInput = document.getElementById('unitContact');

    if (nameInput) nameInput.value = data.name || '';
    if (addrInput) addrInput.value = data.address || '';
    if (phoneInput) phoneInput.value = data.phone || '';
    if (emailInput) emailInput.value = data.email || '';
    if (contactInput) contactInput.value = data.contact || '';
}

window.saveUnit = function() {
    const name = document.getElementById('unitName').value;
    const address = document.getElementById('unitAddress').value;
    const phone = document.getElementById('unitPhone').value;
    const email = document.getElementById('unitEmail').value;
    const contact = document.getElementById('unitContact').value;

    if (!name || !address || !phone || !email || !contact) {
        alert('Vui lòng điền đầy đủ các trường bắt buộc (*)');
        return;
    }

    const payload = {
        id: currentId,
        type: currentType,
        name: name,
        address: address,
        phone: phone,
        email: email,
        contact: contact
    };

    fetch('/api/don-vi/upsert/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            App.showSuccess(data.message, () => {
                closeUnitModal();
                loadUnits(currentPage);
            });
        } else {
            alert('Lỗi: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Đã xảy ra lỗi khi gửi yêu cầu.');
    });
}

window.closeDeleteModal = function() {
    App.closePopup();
}

document.addEventListener('DOMContentLoaded', function () {
    console.log('DOMContentLoaded fired');
    const searchForm = document.querySelector('.search-row');
    if (searchForm) {
        searchForm.onsubmit = (e) => {
            e.preventDefault();
            loadUnits(1);
        };
    }

    const addBtn = document.querySelector('.btn-green');
    if (addBtn) {
        addBtn.onclick = function (e) {
            e.preventDefault();
            currentId = null;
            document.getElementById('unitName').value = '';
            document.getElementById('unitAddress').value = '';
            document.getElementById('unitPhone').value = '';
            document.getElementById('unitEmail').value = '';
            document.getElementById('unitContact').value = '';

            const inputs = document.getElementById('modalUnit').querySelectorAll('input');
            inputs.forEach(i => i.disabled = false);
            const saveBtn = document.getElementById('btnSaveUnit');
            if (saveBtn) saveBtn.style.display = 'block';

            openUnitModal('Thêm mới đơn vị');
        };
    }
});
