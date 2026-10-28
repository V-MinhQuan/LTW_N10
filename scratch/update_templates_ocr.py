import os

# 1. Update van_ban_den/index.html
with open('QLVB/templates/van_ban_den/index.html', 'r', encoding='utf-8') as f:
    vbd_html = f.read()

target1 = """              <i class="fas fa-trash-alt vbd-file-delete" onclick="removeAddSelectedFile()" title="Bỏ chọn tệp"></i>
            </div>
          </div>"""

replacement1 = """              <div style="display: flex; align-items: center; gap: 8px;">
                <button type="button" class="btn btn-sm" style="background: #f0fdf4; border: 1px solid #86efac; color: #166534; padding: 4px 10px; font-size: 12px; font-weight: 600; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; gap: 4px;" onclick="quyetDuLieuOCRVanBanDen()" title="Quét lại OCR">
                  <i class="fas fa-magic"></i> Quét lại OCR
                </button>
                <i class="fas fa-trash-alt vbd-file-delete" onclick="removeAddSelectedFile()" title="Bỏ chọn tệp"></i>
              </div>
            </div>
          </div>"""

vbd_norm = vbd_html.replace('\r\n', '\n')
target1_norm = target1.replace('\r\n', '\n')
replacement1_norm = replacement1.replace('\r\n', '\n')

if target1_norm in vbd_norm:
    vbd_norm = vbd_norm.replace(target1_norm, replacement1_norm, 1)
    with open('QLVB/templates/van_ban_den/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(vbd_norm)
    print("SUCCESS: Updated van_ban_den/index.html")
else:
    print("FAILED: target1 not found in van_ban_den/index.html")

# 2. Update van_ban_di/index.html
with open('QLVB/templates/van_ban_di/index.html', 'r', encoding='utf-8') as f:
    di_html = f.read()

target2 = """      <div class="vbd-upload-area-new" style="width: 100%; box-sizing: border-box;">
        <div class="upload-icon">
          <i class="fa fa-cloud-upload-alt"></i>
        </div>
        <p id="fileLabel">Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính</p>
        <input type="file" id="fileInput" style="display:none"
          onchange="document.getElementById('fileLabel').innerHTML = this.files[0] ? this.files[0].name : 'Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính'">
        <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 6px;">
          <button type="button" class="btn-attach-new" onclick="document.getElementById('fileInput').click()">
            <i class="fas fa-paperclip"></i> Chọn từ máy tính
          </button>
          <button type="button" class="btn-attach-new" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);" onclick="tuDongTaoVaDinhKemDocx('create')">
            <i class="fas fa-magic"></i> Sinh mẫu Word
          </button>
          <button type="button" class="btn-attach-new" style="background: #0284c7;" onclick="taiBieuMauWord('create')">
            <i class="fas fa-download"></i> Tải mẫu Word
          </button>
        </div>
      </div>"""

replacement2 = """      <div class="vbd-upload-area-new" id="vbd_modal_upload_area" style="width: 100%; box-sizing: border-box;">
        <div class="upload-icon">
          <i class="fa fa-cloud-upload-alt"></i>
        </div>
        <p id="fileLabel">Kéo thả tệp tin vào đây hoặc nhấn nút<br>bên dưới để chọn tệp từ máy tính</p>
        <input type="file" id="fileInput" style="display:none" onchange="xuLyTepDinhKemVanBanDi(this)">
        <div style="display: flex; gap: 8px; justify-content: center; flex-wrap: wrap; margin-top: 6px;">
          <button type="button" class="btn-attach-new" onclick="document.getElementById('fileInput').click()">
            <i class="fas fa-paperclip"></i> Chọn từ máy tính
          </button>
          <button type="button" class="btn-attach-new" style="background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);" id="btnOcrScanVBD" onclick="quyetDuLieuOCRVanBanDi()">
            <i class="fas fa-magic"></i> Quét OCR & Điền tự động
          </button>
          <button type="button" class="btn-attach-new" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);" onclick="tuDongTaoVaDinhKemDocx('create')">
            <i class="fas fa-file-word"></i> Sinh mẫu Word
          </button>
        </div>
      </div>
      <div id="vbd_ocr_status_badge" style="display:none; width: 100%; margin-top: 8px; padding: 10px 14px; border-radius: 6px; font-size: 13px; background: #f0fdf4; border: 1px solid #86efac; color: #166534; box-sizing: border-box;">
        <i class="fas fa-check-circle text-success me-1"></i> <span id="vbd_ocr_status_text">Đã trích xuất thông tin thành công!</span>
      </div>"""

di_norm = di_html.replace('\r\n', '\n')
target2_norm = target2.replace('\r\n', '\n')
replacement2_norm = replacement2.replace('\r\n', '\n')

if target2_norm in di_norm:
    di_norm = di_norm.replace(target2_norm, replacement2_norm, 1)
    with open('QLVB/templates/van_ban_di/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(di_norm)
    print("SUCCESS: Updated van_ban_di/index.html")
else:
    print("FAILED: target2 not found in van_ban_di/index.html")

