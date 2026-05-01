import io
with io.open('d:/LTW_Nhom10/QLVB/templates/van_ban_di/index.html', 'r', encoding='utf-8') as f:
    c = f.read()
c = c.replace('<select id="edit_donViNgoai" class="form-control" onchange="checkEditDonVi()">', '<select id="edit_donViNgoai" class="form-control">')
c = c.replace('<select id="edit_donViBH" class="form-control" onchange="checkEditDonVi()">', '<select id="edit_donViBH" class="form-control">')
c = c.replace('<span style="font-weight:normal; font-size:12px; color:#666;">(Chọn 1 trong 2)</span>', '(<span style="color:red">*</span>)')
c = c.replace('<span style="font-weight:normal; font-size:12px; color:#666;"></span>', '(<span style="color:red">*</span>)')
with io.open('d:/LTW_Nhom10/QLVB/templates/van_ban_di/index.html', 'w', encoding='utf-8') as f:
    f.write(c)
