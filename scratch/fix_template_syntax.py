import os

# 1. Fix van_ban_den/index.html
with open('QLVB/templates/van_ban_den/index.html', 'r', encoding='utf-8') as f:
    text_den = f.read()

text_den = text_den.replace(
    '{% if request.GET.trang_thai=="DANG_XU_LY" %}',
    '{% if request.GET.trang_thai == "DANG_XU_LY" %}'
)
text_den = text_den.replace(
    '{% if request.GET.trang_thai=="HOAN_THANH" %}',
    '{% if request.GET.trang_thai == "HOAN_THANH" %}'
)

with open('QLVB/templates/van_ban_den/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_den)
print("Updated van_ban_den/index.html")

# 2. Fix van_ban_di/index.html
with open('QLVB/templates/van_ban_di/index.html', 'r', encoding='utf-8') as f:
    text_di = f.read()

text_di = text_di.replace(
    '{% if loai_vb==lv %}',
    '{% if loai_vb == lv %}'
)
text_di = text_di.replace(
    '{% if trang_thai=="DU_THAO" %}',
    '{% if trang_thai == "DU_THAO" %}'
)
text_di = text_di.replace(
    '{% if trang_thai=="CHO_PHE_DUYET" %}',
    '{% if trang_thai == "CHO_PHE_DUYET" %}'
)
text_di = text_di.replace(
    '{% if trang_thai=="DA_PHE_DUYET" %}',
    '{% if trang_thai == "DA_PHE_DUYET" %}'
)
text_di = text_di.replace(
    '{% if trang_thai=="DA_PHAT_HANH" %}',
    '{% if trang_thai == "DA_PHAT_HANH" %}'
)

with open('QLVB/templates/van_ban_di/index.html', 'w', encoding='utf-8', newline='\r\n') as f:
    f.write(text_di)
print("Updated van_ban_di/index.html")

