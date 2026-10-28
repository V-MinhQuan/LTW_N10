with open('QLVB/web/ai_services.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = """        summary_data = {
            'muc_dich_cot_loi': f"Thực hiện '{trich_yeu or loai_vb}' thuộc lĩnh vực {classification['linh_vuc']}.",
            'linh_vuc': classification['linh_vuc'],"""

replacement = """        real_trich_yeu = trich_yeu
        ty_m = re.search(r'(?:V/v|Về việc|Nội dung)\s*[:.]?\s*([^\\n\\r]+)', content, re.IGNORECASE)
        if ty_m and len(ty_m.group(1).strip(" .-_*")) > 5:
            real_trich_yeu = ty_m.group(1).strip(" .-_*")

        summary_data = {
            'muc_dich_cot_loi': f"Thực hiện '{real_trich_yeu or loai_vb}' thuộc lĩnh vực {classification['linh_vuc']}.",
            'linh_vuc': classification['linh_vuc'],"""

text_norm = text.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

assert target_norm in text_norm, 'target not found in ai_services.py'
text_norm = text_norm.replace(target_norm, replacement_norm, 1)

with open('QLVB/web/ai_services.py', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_norm)
print('Updated real_trich_yeu in ai_services.py!')

