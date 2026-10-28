"""
Module tự động sinh tệp Word (.docx) chuẩn nhận diện Vietasia Travel
Theo thể thức văn bản hành chính Việt Nam (Nghị định 30/2020/NĐ-CP)
Phục vụ tính năng AUTO-03: Tự động sinh văn bản từ Biểu mẫu chuẩn
"""

import io
from datetime import datetime
from docx import Document
from docx.shared import Inches, Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn


def _set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Thiết lập padding cho ô trong bảng"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)


def _set_table_borders_none(table):
    """Xóa toàn bộ viền bảng để làm layout chia 2 cột"""
    tblPr = table._tbl.tblPr
    tblBorders = tblPr.find(qn('w:tblBorders'))
    if tblBorders is not None:
        tblPr.remove(tblBorders)
    tblBorders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="none"/>'
        f'<w:left w:val="none"/>'
        f'<w:bottom w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="none"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(tblBorders)


def generate_docx_template(loai_vb, so_ky_hieu, trich_yeu, don_vi_nhan="Quý cơ quan / Đơn vị", nguoi_soan=None, nguoi_ky="Đỗ Ngọc Hà", ngay_ban_hanh=None):
    """
    Sinh tài liệu Word theo đúng chuẩn mẫu văn bản Vietasia Travel
    """
    doc = Document()

    # 1. Thiết lập lề trang chuẩn Nghị định 30/2020/NĐ-CP
    sections = doc.sections
    for section in sections:
        section.top_margin = Cm(2.0)
        section.bottom_margin = Cm(2.0)
        section.left_margin = Cm(3.0)
        section.right_margin = Cm(2.0)
        section.page_width = Cm(21.0)
        section.page_height = Cm(29.7)

    # Đặt font chữ mặc định Times New Roman
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Times New Roman'
    font.size = Pt(13)
    font.color.rgb = RGBColor(0, 0, 0)

    # 2. Xử lý ngày tháng
    now = datetime.now()
    if ngay_ban_hanh:
        if isinstance(ngay_ban_hanh, str):
            try:
                dt = datetime.strptime(ngay_ban_hanh, '%Y-%m-%d')
            except ValueError:
                dt = now
        elif hasattr(ngay_ban_hanh, 'day'):
            dt = ngay_ban_hanh
        else:
            dt = now
    else:
        dt = now

    ngay_str = f"Hà Nội, ngày {dt.day:02d} tháng {dt.month:02d} năm {dt.year}"

    # 3. HEADER TABLE: 2 Cột (Trái: Tên Cơ quan & Số hiệu | Phải: Quốc hiệu & Địa danh ngày tháng)
    table_hdr = doc.add_table(rows=1, cols=2)
    table_hdr.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders_none(table_hdr)
    
    col_widths = (Cm(7.5), Cm(8.5))
    for row in table_hdr.rows:
        for i, w in enumerate(col_widths):
            row.cells[i].width = w

    cell_left = table_hdr.cell(0, 0)
    cell_right = table_hdr.cell(0, 1)

    # Cột trái
    p_cq = cell_left.paragraphs[0]
    p_cq.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cq.paragraph_format.space_before = Pt(0)
    p_cq.paragraph_format.space_after = Pt(2)
    run_cq1 = p_cq.add_run("CÔNG TY CỔ PHẦN DU LỊCH & DỊCH VỤ")
    run_cq1.font.size = Pt(10)
    run_cq1.font.name = 'Times New Roman'
    run_cq1.bold = True

    p_cq2 = cell_left.add_paragraph()
    p_cq2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cq2.paragraph_format.space_before = Pt(0)
    p_cq2.paragraph_format.space_after = Pt(6)
    run_cq2 = p_cq2.add_run("VIETASIA TRAVEL")
    run_cq2.font.size = Pt(12)
    run_cq2.font.name = 'Times New Roman'
    run_cq2.bold = True
    run_cq2.font.color.rgb = RGBColor(14, 112, 166)  # Xanh Vietasia

    p_skh = cell_left.add_paragraph()
    p_skh.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_skh.paragraph_format.space_before = Pt(2)
    p_skh.paragraph_format.space_after = Pt(0)
    run_skh = p_skh.add_run(f"Số: {so_ky_hieu or '.../CV-VAT-2026'}")
    run_skh.font.size = Pt(11)
    run_skh.font.name = 'Times New Roman'
    run_skh.bold = True

    # Cột phải
    p_qh1 = cell_right.paragraphs[0]
    p_qh1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh1.paragraph_format.space_before = Pt(0)
    p_qh1.paragraph_format.space_after = Pt(2)
    run_qh1 = p_qh1.add_run("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    run_qh1.font.size = Pt(11)
    run_qh1.font.name = 'Times New Roman'
    run_qh1.bold = True

    p_qh2 = cell_right.add_paragraph()
    p_qh2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qh2.paragraph_format.space_before = Pt(0)
    p_qh2.paragraph_format.space_after = Pt(4)
    run_qh2 = p_qh2.add_run("Độc lập - Tự do - Hạnh phúc")
    run_qh2.font.size = Pt(12)
    run_qh2.font.name = 'Times New Roman'
    run_qh2.bold = True
    run_qh2.underline = True

    p_date = cell_right.add_paragraph()
    p_date.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_date.paragraph_format.space_before = Pt(4)
    p_date.paragraph_format.space_after = Pt(0)
    run_date = p_date.add_run(ngay_str)
    run_date.font.size = Pt(12)
    run_date.font.name = 'Times New Roman'
    run_date.italic = True

    # Đường phân cách nhẹ
    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # 4. TIÊU ĐỀ & NỘI DUNG VĂN BẢN THEO LOẠI
    loai_lower = (loai_vb or 'công văn').lower()

    if 'quyết định' in loai_lower or 'quyet dinh' in loai_lower or 'qd' in loai_lower:
        _build_quyet_dinh(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky)
    elif 'tờ trình' in loai_lower or 'to trinh' in loai_lower or 'ttr' in loai_lower:
        _build_to_trinh(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_soan or "Người lập tờ trình")
    elif 'thông báo' in loai_lower or 'thong bao' in loai_lower or 'tb' in loai_lower:
        _build_thong_bao(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky)
    elif 'báo cáo' in loai_lower or 'bao cao' in loai_lower or 'bc' in loai_lower:
        _build_bao_cao(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_soan or "Người báo cáo")
    elif 'hợp đồng' in loai_lower or 'hop dong' in loai_lower or 'hd' in loai_lower:
        _build_hop_dong(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky)
    else:
        # Mặc định là Công văn
        _build_cong_van(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky)

    # Xuất ra buffer BytesIO
    target_stream = io.BytesIO()
    doc.save(target_stream)
    target_stream.seek(0)
    return target_stream


def _build_cong_van(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky):
    """Biểu mẫu Công văn"""
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_before = Pt(8)
    p_title.paragraph_format.space_after = Pt(12)
    p_title.paragraph_format.line_spacing = 1.2
    run_vv = p_title.add_run(f"V/v: {trich_yeu or 'Thực hiện nhiệm vụ công tác'}")
    run_vv.bold = True
    run_vv.font.size = Pt(13)

    p_kg = doc.add_paragraph()
    p_kg.paragraph_format.space_before = Pt(6)
    p_kg.paragraph_format.space_after = Pt(12)
    run_kg = p_kg.add_run(f"Kính gửi: {don_vi_nhan or 'Quý đối tác / Đơn vị'}")
    run_kg.bold = True

    # Nội dung chính
    p_body1 = doc.add_paragraph()
    p_body1.paragraph_format.line_spacing = 1.25
    p_body1.paragraph_format.space_after = Pt(8)
    p_body1.add_run("Công ty Cổ phần Du lịch và Dịch vụ Vietasia xin gửi lời chào trân trọng và lời chúc hợp tác thành công đến Quý đơn vị.")

    p_body2 = doc.add_paragraph()
    p_body2.paragraph_format.line_spacing = 1.25
    p_body2.paragraph_format.space_after = Pt(8)
    p_body2.add_run(f"Liên quan đến nội dung '{trich_yeu or 'nhiệm vụ phối hợp'}', Công ty Vietasia xin thông tin và đề nghị Quý đơn vị phối hợp triển khai các nội dung sau:")

    for item in [
        "1. Tiếp nhận và rà soát hồ sơ, phương án tổ chức chi tiết đính kèm theo công văn này.",
        "2. Cử đầu mối chuyên môn phối hợp cùng Vietasia Travel để thống nhất kế hoạch triển khai.",
        "3. Phản hồi bằng văn bản hoặc gửi xác nhận về Công ty trước ngày [Thời hạn phản hồi]."
    ]:
        p_item = doc.add_paragraph()
        p_item.paragraph_format.left_indent = Cm(0.8)
        p_item.paragraph_format.line_spacing = 1.25
        p_item.paragraph_format.space_after = Pt(4)
        p_item.add_run(item)

    p_body3 = doc.add_paragraph()
    p_body3.paragraph_format.line_spacing = 1.25
    p_body3.paragraph_format.space_before = Pt(8)
    p_body3.paragraph_format.space_after = Pt(18)
    p_body3.add_run("Công ty Vietasia Travel rất mong nhận được sự phối hợp chặt chẽ từ Quý đơn vị. Trân trọng cảm ơn!")

    _build_footer_signature(doc, left_text="Nơi nhận:\n- Như trên;\n- Ban Giám đốc (để b/c);\n- Lưu: VT, HS.", right_role="TỔNG GIÁM ĐỐC", signer_name=nguoi_ky or "Đỗ Ngọc Hà")


def _build_quyet_dinh(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky):
    """Biểu mẫu Quyết định"""
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_main.paragraph_format.space_before = Pt(8)
    p_main.paragraph_format.space_after = Pt(4)
    run_main = p_main.add_run("QUYẾT ĐỊNH")
    run_main.bold = True
    run_main.font.size = Pt(15)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(14)
    run_sub = p_sub.add_run(f"Về việc {trich_yeu or 'phê duyệt chủ trương công tác'}")
    run_sub.bold = True
    run_sub.italic = True
    run_sub.font.size = Pt(13)

    p_auth = doc.add_paragraph()
    p_auth.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_auth.paragraph_format.space_after = Pt(10)
    run_auth = p_auth.add_run("TỔNG GIÁM ĐỐC CÔNG TY CP DU LỊCH & DỊCH VỤ VIETASIA")
    run_auth.bold = True

    for cc in [
        "- Căn cứ Điều lệ tổ chức và hoạt động của Công ty Cổ phần Du lịch và Dịch vụ Vietasia;",
        "- Căn cứ Quy chế quản lý văn bản, điều hành và phân công trách nhiệm của Ban Giám đốc;",
        "- Xét đề nghị của Trưởng các phòng ban chuyên môn liên quan.",
    ]:
        p_cc = doc.add_paragraph()
        p_cc.paragraph_format.line_spacing = 1.2
        p_cc.paragraph_format.space_after = Pt(3)
        p_cc.italic = True
        p_cc.add_run(cc)

    p_qd = doc.add_paragraph()
    p_qd.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_qd.paragraph_format.space_before = Pt(10)
    p_qd.paragraph_format.space_after = Pt(10)
    run_qd = p_qd.add_run("QUYẾT ĐỊNH:")
    run_qd.bold = True

    dieu1 = doc.add_paragraph()
    dieu1.paragraph_format.line_spacing = 1.25
    dieu1.paragraph_format.space_after = Pt(6)
    r_d1 = dieu1.add_run("Điều 1. ")
    r_d1.bold = True
    dieu1.add_run(f"Phê duyệt và ban hành quy định về '{trich_yeu or 'nội dung nhiệm vụ'}'.")

    dieu2 = doc.add_paragraph()
    dieu2.paragraph_format.line_spacing = 1.25
    dieu2.paragraph_format.space_after = Pt(6)
    r_d2 = dieu2.add_run("Điều 2. ")
    r_d2.bold = True
    dieu2.add_run("Quyết định này có hiệu lực thi hành kể từ ngày ký. Mọi văn bản và quy định trái với quyết định này trước đây đều bãi bỏ.")

    dieu3 = doc.add_paragraph()
    dieu3.paragraph_format.line_spacing = 1.25
    dieu3.paragraph_format.space_after = Pt(18)
    r_d3 = dieu3.add_run("Điều 3. ")
    r_d3.bold = True
    dieu3.add_run(f"Các phòng ban chuyên môn, các đơn vị trực thuộc và cá nhân liên quan chịu trách nhiệm thi hành Quyết định này.")

    _build_footer_signature(doc, left_text="Nơi nhận:\n- Như Điều 3;\n- HĐQT (để b/c);\n- Lưu: VT, TCHC.", right_role="TỔNG GIÁM ĐỐC", signer_name=nguoi_ky or "Đỗ Ngọc Hà")


def _build_to_trinh(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_soan):
    """Biểu mẫu Tờ trình"""
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_main.paragraph_format.space_before = Pt(8)
    p_main.paragraph_format.space_after = Pt(4)
    run_main = p_main.add_run("TỜ TRÌNH")
    run_main.bold = True
    run_main.font.size = Pt(15)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run(f"Về việc {trich_yeu or 'phê duyệt phương án công tác'}")
    run_sub.bold = True
    run_sub.italic = True

    p_kg = doc.add_paragraph()
    p_kg.paragraph_format.space_after = Pt(12)
    run_kg = p_kg.add_run("Kính gửi: Ban Giám đốc Công ty CP Du lịch & Dịch vụ Vietasia")
    run_kg.bold = True

    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.25
    p1.paragraph_format.space_after = Pt(6)
    p1.add_run(f"Căn cứ vào kế hoạch công tác và yêu cầu thực tiễn hoạt động của đơn vị, kính trình Ban Giám đốc xem xét phê duyệt nội dung: '{trich_yeu}'.")

    p2 = doc.add_paragraph()
    p2.paragraph_format.line_spacing = 1.25
    p2.paragraph_format.space_after = Pt(6)
    r2 = p2.add_run("I. Sự cần thiết và căn cứ pháp lý / thực tiễn:\n")
    r2.bold = True
    p2.add_run("[Trình bày chi tiết lý do và bối cảnh cần triển khai đề xuất...]")

    p3 = doc.add_paragraph()
    p3.paragraph_format.line_spacing = 1.25
    p3.paragraph_format.space_after = Pt(6)
    r3 = p3.add_run("II. Nội dung đề xuất cụ thể:\n")
    r3.bold = True
    p3.add_run("[Liệt kê phương án, kinh phí dự kiến, nhân sự phụ trách và tiến độ...]")

    p4 = doc.add_paragraph()
    p4.paragraph_format.line_spacing = 1.25
    p4.paragraph_format.space_after = Pt(18)
    r4 = p4.add_run("III. Kiến nghị:\n")
    r4.bold = True
    p4.add_run("Kính đề nghị Ban Giám đốc xem xét, có ý kiến chỉ đạo và phê duyệt để đơn vị có cơ sở triển khai thực hiện.")

    _build_footer_signature(doc, left_text="Nơi nhận:\n- Như trên;\n- Lưu: VT, ĐV.", right_role="NGƯỜI TRÌNH", signer_name=nguoi_soan or "Người soạn thảo")


def _build_thong_bao(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky):
    """Biểu mẫu Thông báo"""
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_main.paragraph_format.space_before = Pt(8)
    p_main.paragraph_format.space_after = Pt(4)
    run_main = p_main.add_run("THÔNG BÁO")
    run_main.bold = True
    run_main.font.size = Pt(15)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run(f"Về việc {trich_yeu or 'thông báo kế hoạch hoạt động'}")
    run_sub.bold = True
    run_sub.italic = True

    p_kg = doc.add_paragraph()
    p_kg.paragraph_format.space_after = Pt(12)
    run_kg = p_kg.add_run(f"Kính gửi: {don_vi_nhan or 'Toàn thể Cán bộ nhân viên Công ty Vietasia Travel'}")
    run_kg.bold = True

    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.25
    p1.paragraph_format.space_after = Pt(8)
    p1.add_run(f"Ban Giám đốc Công ty Vietasia Travel xin trân trọng thông báo đến Quý đơn vị/các phòng ban về việc: '{trich_yeu}' với các nội dung cụ thể sau:")

    for item in [
        "1. Kế hoạch và thời gian bắt đầu triển khai: [Nhập thời gian cụ thể].",
        "2. Đối tượng và phạm vi áp dụng: [Nhập danh sách phòng ban / đối tượng].",
        "3. Yêu cầu phối hợp: Các bộ phận liên quan nghiêm túc thực hiện đúng tiến độ được giao."
    ]:
        pi = doc.add_paragraph()
        pi.paragraph_format.left_indent = Cm(0.8)
        pi.paragraph_format.line_spacing = 1.25
        pi.paragraph_format.space_after = Pt(4)
        pi.add_run(item)

    doc.add_paragraph().paragraph_format.space_after = Pt(14)
    _build_footer_signature(doc, left_text="Nơi nhận:\n- Như trên;\n- Ban Giám đốc;\n- Lưu: VT.", right_role="TỔNG GIÁM ĐỐC", signer_name=nguoi_ky or "Đỗ Ngọc Hà")


def _build_bao_cao(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_soan):
    """Biểu mẫu Báo cáo"""
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_main.paragraph_format.space_before = Pt(8)
    p_main.paragraph_format.space_after = Pt(4)
    run_main = p_main.add_run("BÁO CÁO")
    run_main.bold = True
    run_main.font.size = Pt(15)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run(f"Về việc {trich_yeu or 'tổng kết tình hình thực hiện công tác'}")
    run_sub.bold = True
    run_sub.italic = True

    p_kg = doc.add_paragraph()
    p_kg.paragraph_format.space_after = Pt(12)
    run_kg = p_kg.add_run("Kính gửi: Ban Giám đốc Công ty CP Du lịch & Dịch vụ Vietasia")
    run_kg.bold = True

    p1 = doc.add_paragraph()
    p1.paragraph_format.line_spacing = 1.25
    p1.paragraph_format.space_after = Pt(8)
    p1.add_run(f"Đơn vị xin báo cáo tổng hợp tiến độ và kết quả thực hiện nhiệm vụ: '{trich_yeu}':")

    for part in ["I. Kết quả thực hiện:", "II. Khó khăn, vướng mắc phát sinh:", "III. Đề xuất & Kiến nghị tiếp theo:"]:
        pp = doc.add_paragraph()
        pp.paragraph_format.space_before = Pt(6)
        pp.paragraph_format.space_after = Pt(4)
        rr = pp.add_run(part)
        rr.bold = True
        p_c = doc.add_paragraph()
        p_c.paragraph_format.left_indent = Cm(0.8)
        p_c.paragraph_format.space_after = Pt(6)
        p_c.add_run("[Nội dung chi tiết...]")

    _build_footer_signature(doc, left_text="Nơi nhận:\n- Như trên;\n- Lưu: VT.", right_role="NGƯỜI LẬP BÁO CÁO", signer_name=nguoi_soan or "Người báo cáo")


def _build_hop_dong(doc, so_ky_hieu, trich_yeu, don_vi_nhan, nguoi_ky):
    """Biểu mẫu Hợp đồng"""
    p_main = doc.add_paragraph()
    p_main.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_main.paragraph_format.space_before = Pt(8)
    p_main.paragraph_format.space_after = Pt(4)
    run_main = p_main.add_run("HỢP ĐỒNG HỢP TÁC KINH DOANH DỊCH VỤ")
    run_main.bold = True
    run_main.font.size = Pt(15)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run(f"Số: {so_ky_hieu or '.../HĐ-VAT-2026'}")
    run_sub.bold = True

    doc.add_paragraph("Hôm nay, hai bên gồm có:").paragraph_format.space_after = Pt(6)

    # Bên A
    p_a = doc.add_paragraph()
    p_a.paragraph_format.space_after = Pt(4)
    ra = p_a.add_run("BÊN A: CÔNG TY CỔ PHẦN DU LỊCH & DỊCH VỤ VIETASIA\n")
    ra.bold = True
    p_a.add_run(f"Đại diện: Ông/Bà {nguoi_ky or 'Đỗ Ngọc Hà'} - Chức vụ: Tổng Giám đốc\nĐịa chỉ: Hà Nội\nĐiện thoại: 024.xxxx.xxxx")

    # Bên B
    p_b = doc.add_paragraph()
    p_b.paragraph_format.space_after = Pt(10)
    rb = p_b.add_run(f"BÊN B: {don_vi_nhan or 'ĐỐI TÁC'}\n")
    rb.bold = True
    p_b.add_run("Đại diện: [Người đại diện] - Chức vụ: [Chức vụ]\nĐịa chỉ: [Địa chỉ]\nĐiện thoại: [Điện thoại]")

    p_c = doc.add_paragraph()
    p_c.paragraph_format.space_after = Pt(14)
    p_c.add_run(f"Hai bên cùng thống nhất ký kết hợp đồng với nội dung: '{trich_yeu}' theo các điều khoản dịch vụ chi tiết đính kèm.")

    _build_footer_signature(doc, left_text="ĐẠI DIỆN BÊN B\n(Ký và ghi rõ họ tên)", right_role="ĐẠI DIỆN BÊN A\nTỔNG GIÁM ĐỐC", signer_name=nguoi_ky or "Đỗ Ngọc Hà")


def _build_footer_signature(doc, left_text, right_role, signer_name):
    """Bảng chữ ký 2 cột chuẩn Nghị định 30"""
    tbl = doc.add_table(rows=1, cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    _set_table_borders_none(tbl)

    for row in tbl.rows:
        row.cells[0].width = Cm(8.0)
        row.cells[1].width = Cm(8.0)

    # Cột trái
    c_left = tbl.cell(0, 0)
    p_l = c_left.paragraphs[0]
    p_l.paragraph_format.line_spacing = 1.15
    for line in left_text.split('\n'):
        r = p_l.add_run(line + '\n')
        r.font.size = Pt(10)
        r.font.name = 'Times New Roman'
        if 'Nơi nhận' in line or 'ĐẠI DIỆN' in line:
            r.bold = True
        else:
            r.italic = True

    # Cột phải
    c_right = tbl.cell(0, 1)
    p_r = c_right.paragraphs[0]
    p_r.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_r.paragraph_format.line_spacing = 1.15
    r_role = p_r.add_run(right_role + '\n\n\n\n')
    r_role.bold = True
    r_role.font.size = Pt(12)
    r_role.font.name = 'Times New Roman'

    r_name = p_r.add_run(signer_name)
    r_name.bold = True
    r_name.font.size = Pt(13)
    r_name.font.name = 'Times New Roman'

