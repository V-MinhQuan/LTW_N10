console.log('quan_ly_don_vi.js loaded v2');

// Note: App.confirm and App.confirmDelete have been migrated to base.html for global use.

let currentId = null;
let currentType = location.href.includes('ben-trong') ? 'trong' : 'ngoai';
let currentPage = 1;

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
    currentPage = page;
    const name = document.querySelector('input[name="name"]')?.value || '';
    const address = document.querySelector('input[name="address"]')?.value || '';
    const contact = document.querySelector('input[name="contact"]')?.value || '';
    const status = document.querySelector('select[name="status"]')?.value || 'ALL';

    const url = `${window.location.pathname}?page=${page}&ajax=1&name=${encodeURIComponent(name)}&address=${encodeURIComponent(address)}&contact=${encodeURIComponent(contact)}&status=${encodeURIComponent(status)}`;
    
    fetch(url)
        .then(response => response.json())
        .then(result => {
            if (result.status === 'success') {
                renderTable(result.data, result.pagination);
                renderPagination(result.pagination);
                const totalElem = document.getElementById('tableTotal');
                if (totalElem) totalElem.innerText = `Tổng số: ${result.pagination.total_count}`;
            }
        });
}

function renderTable(units, pagination) {
    const tbody = document.getElementById('unitTableBody');
    if (!tbody) return;
    tbody.innerHTML = '';
    const startSTT = (pagination.current_page - 1) * 5 + 1;

    units.forEach((unit, index) => {
        const tr = document.createElement('tr');
        const isInactive = unit.status === 'INACTIVE';
        
        // Actions: ACTIVE units show View/Edit. INACTIVE units show View/Edit/Restore (Yellow).
        const restoreBtn = isInactive
            ? `<button type="button" class="action-btn btn-warning" onclick="window.confirmReactivateById(${unit.id})" title="Khôi phục"><i class="fas fa-rotate-left"></i></button>`
            : '';

        tr.innerHTML = `
            <td class="col-stt">${startSTT + index}</td>
            <td style="text-align: left;"><a href="javascript:void(0)" class="text-blue" onclick="window.viewUnitById(${unit.id})">${unit.name}</a></td>
            <td class="text-left">${unit.address || ''}</td>
            <td class="text-left">${unit.phone || ''}</td>
            <td class="text-left">${unit.email || ''}</td>
            <td class="text-left">${unit.contact || ''}</td>
            <td class="col-status">${!isInactive ? '<span class="status-pill pill-green">Đang hợp tác</span>' : '<span class="status-pill pill-gray">Ngừng hợp tác</span>'}</td>
            <td class="col-actions">
                <button type="button" class="action-btn btn-primary" onclick="window.viewUnitById(${unit.id})" title="Xem"><i class="fas fa-eye"></i></button>
                <button type="button" class="action-btn btn-success" onclick="window.editUnitById(${unit.id})" title="Sửa"><i class="fas fa-edit"></i></button>
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
    
    const addBtn = (text, page, active) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = `page-btn ${active ? 'active' : ''}`;
        btn.innerText = text;
        if (!active) btn.onclick = () => window.loadUnits(page);
        container.appendChild(btn);
    }
    
    addBtn('Đầu', 1);
    if (pagination.current_page > 1) {
        addBtn('Trước', pagination.current_page - 1);
    }

    let startPage = Math.max(1, pagination.current_page - 2);
    let endPage = Math.min(pagination.total_pages, startPage + 4);
    if (endPage - startPage < 4) {
        startPage = Math.max(1, endPage - 4);
    }

    for (let i = startPage; i <= endPage; i++) {
        if (i >= 1 && i <= pagination.total_pages) {
            addBtn(i, i, i === pagination.current_page);
        }
    }

    if (pagination.current_page < pagination.total_pages) {
        addBtn('Sau', pagination.current_page + 1);
    }
    addBtn('Cuối', pagination.total_pages);
}

window.viewUnitById = function(id) {
    fetch(`${window.location.pathname}?id=${id}&ajax=1`).then(r => r.json()).then(res => {
        populateModal(res.data[0]);
        document.getElementById('modalUnit').querySelectorAll('input').forEach(i => i.disabled = true);
        document.getElementById('btnSaveUnit').style.display = 'none';
        document.getElementById('btnDeactivateModal').style.display = 'none'; // Hide in View mode
        window.openUnitModal('Chi tiết đơn vị');
    });
};

window.editUnitById = function(id) {
    currentId = id;
    fetch(`${window.location.pathname}?id=${id}&ajax=1`).then(r => r.json()).then(res => {
        const unit = res.data[0];
        populateModal(unit);
        document.getElementById('modalUnit').querySelectorAll('input').forEach(i => i.disabled = false);
        document.getElementById('btnSaveUnit').style.display = 'block';
        
        // Show Deactivate button only if unit is ACTIVE
        const deactBtn = document.getElementById('btnDeactivateModal');
        if (deactBtn) {
            deactBtn.style.display = (unit.status === 'ACTIVE') ? 'block' : 'none';
        }
        
        window.openUnitModal('Chỉnh sửa đơn vị');
    });
};

window.handleDeactivateFromModal = function() {
    if (!currentId) return;
    window.confirmDeactivateById(currentId);
}

window.confirmDeactivateById = function(id) {
    console.log('Action: confirmDeactivateById', id);
    if (window.App && window.App.confirm) {
        window.App.confirm({
            title: "Xác nhận ngừng hợp tác",
            message: "Bạn có chắc muốn ngừng hợp tác với đơn vị này? Dữ liệu vẫn được giữ lại.",
            type: "danger", icon: "fa-ban",
            onConfirm: () => {
                updateUnitStatus(id, 'deactivate');
                window.closeUnitModal();
            }
        });
    }
};

window.confirmReactivateById = function(id) {
    if (window.App && window.App.confirm) {
        window.App.confirm({
            title: "Xác nhận khôi phục",
            message: "Bạn có chắc muốn kích hoạt lại đơn vị này?",
            type: "success", icon: "fa-rotate-left",
            onConfirm: () => updateUnitStatus(id, 'reactivate')
        });
    }
};

window.confirmDeactivate = function(btn) {
    window.confirmDeactivateById(btn.getAttribute('data-id'));
};

window.confirmReactivate = function(btn) {
    window.confirmReactivateById(btn.getAttribute('data-id'));
};

function updateUnitStatus(id, action) {
    fetch('/api/don-vi/delete/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify({ id: id, type: currentType, action: action })
    })
    .then(r => r.json()).then(data => {
        if (data.status === 'success') {
            window.App.showSuccess(data.message, () => window.loadUnits(currentPage));
        }
    });
}

window.viewUnit = function(btn) {
    populateModal(btn.dataset);
    document.getElementById('modalUnit').querySelectorAll('input').forEach(i => i.disabled = true);
    document.getElementById('btnSaveUnit').style.display = 'none';
    document.getElementById('btnDeactivateModal').style.display = 'none';
    window.openUnitModal('Chi tiết đơn vị');
};

window.editUnit = function(btn) {
    const data = btn.dataset;
    currentId = data.id;
    populateModal(data);
    document.getElementById('modalUnit').querySelectorAll('input').forEach(i => i.disabled = false);
    document.getElementById('btnSaveUnit').style.display = 'block';
    
    const deactBtn = document.getElementById('btnDeactivateModal');
    if (deactBtn) {
        deactBtn.style.display = (data.status === 'ACTIVE') ? 'block' : 'none';
    }
    
    window.openUnitModal('Chỉnh sửa đơn vị');
};

function populateModal(data) {
    document.getElementById('unitName').value = data.name || data.TenDonVi || '';
    document.getElementById('unitAddress').value = data.address || data.DiaChi || '';
    document.getElementById('unitPhone').value = data.phone || data.SoDienThoai || '';
    document.getElementById('unitEmail').value = data.email || data.Email || '';
    document.getElementById('unitContact').value = data.contact || data.NguoiLienHe || '';
}

window.saveUnit = function() {
    const name = document.getElementById('unitName').value.trim();
    const address = document.getElementById('unitAddress').value.trim();
    const phone = document.getElementById('unitPhone').value.trim();
    const email = document.getElementById('unitEmail').value.trim();
    const contact = document.getElementById('unitContact').value.trim();

    if (!name || !address || !phone || !email || !contact) {
        window.App.showAlert('Vui lòng điền đầy đủ các thông tin bắt buộc (*)');
        return;
    }

    const payload = {
        id: currentId, type: currentType,
        name: name,
        address: address,
        phone: phone,
        email: email,
        contact: contact
    };
    fetch('/api/don-vi/upsert/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
        body: JSON.stringify(payload)
    }).then(r => r.json()).then(data => {
        if (data.status === 'success') {
            window.App.showSuccess(data.message, () => { window.closeUnitModal(); window.loadUnits(currentPage); });
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded fired v2');
    const searchForm = document.querySelector('.search-row');
    if (searchForm) searchForm.onsubmit = (e) => { e.preventDefault(); window.loadUnits(1); };

    const addBtn = document.querySelector('.btn-green');
    if (addBtn) addBtn.onclick = (e) => {
        e.preventDefault(); currentId = null;
        ['unitName', 'unitAddress', 'unitPhone', 'unitEmail', 'unitContact'].forEach(id => document.getElementById(id).value = '');
        document.getElementById('modalUnit').querySelectorAll('input').forEach(i => i.disabled = false);
        document.getElementById('btnSaveUnit').style.display = 'block';
        
        const deactBtn = document.getElementById('btnDeactivateModal');
        if (deactBtn) deactBtn.style.display = 'none';
        
        window.openUnitModal('Thêm mới đơn vị');
    }
});

console.log('window.confirmDeactivate assigned:', typeof window.confirmDeactivate);
