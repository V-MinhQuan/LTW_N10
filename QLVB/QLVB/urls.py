"""
URL configuration for QLVB project.
... (giữ nguyên phần comment của Django)
"""
from django.contrib import admin
from django.urls import path
from web import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # --- Trang chủ & Xác thực ---
    # Để trống đường dẫn '' để khi vào trang web là hiện trang login ngay
    path('', views.login_view, name='login'),
    path('index/', views.index, name='index'),
    path('logout/', views.logout_view, name='logout'),

    # --- Văn bản đến ---
    path('van-ban-den/', views.van_ban_den_index, name='vbd_index'),

    # --- Văn bản đi ---
    path('van-ban-di/', views.van_ban_di_index, name='vbdi_index'),

    # --- Người dùng ---
    path('quan-ly-nguoi-dung/', views.quan_ly_nguoi_dung_index, name='qlnd_index'),
    # ĐÃ SỬA LẠI THÀNH thong_tin_view VÀ name='thong_tin' ĐỂ KHỚP VỚI VIEWS.PY
    path('quan-ly-nguoi-dung/thong-tin/', views.thong_tin_view, name='thong_tin'),

    # --- Đơn vị ---
    path('quan-ly-don-vi/ben-ngoai/', views.quan_ly_don_vi_ben_ngoai, name='qldv_ngoai'),
    path('quan-ly-don-vi/ben-trong/', views.quan_ly_don_vi_ben_trong, name='qldv_trong'),
    
    # API Đơn vị
    path('api/don-vi/upsert/', views.api_upsert_don_vi, name='api_upsert_don_vi'),
    path('api/don-vi/delete/', views.api_delete_don_vi, name='api_delete_don_vi'),
    
    # API Người dùng
    path('api/nguoi-dung/list/', views.api_nguoi_dung_list, name='api_user_list'),
    path('api/nguoi-dung/upsert/', views.api_upsert_user, name='api_user_upsert'),
    path('api/nguoi-dung/delete/', views.api_delete_user, name='api_user_delete'),
    path('api/vai-tro/list/', views.api_vai_tro_list, name='api_role_list'),

    # --- Xử lý văn bản ---
    path('xu-ly-van-ban/', views.xu_ly_van_ban_index, name='xlvb_index'),
    path('xu-ly-van-ban/bao-cao/', views.xu_ly_van_ban_bao_cao, name='xlvb_bao_cao'),
    path('xu-ly-van-ban/cap-nhat/', views.xu_ly_van_ban_cap_nhat, name='xlvb_cap_nhat'),
    path('xu-ly-van-ban/chuyen-tiep/', views.xu_ly_van_ban_chuyen_tiep, name='xlvb_chuyen_tiep'),
    path('xu-ly-van-ban/phan-cong/', views.xu_ly_van_ban_phan_cong, name='xlvb_phan_cong'),
]