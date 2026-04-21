"""
URL configuration for QLVB project.
... (giữ nguyên phần comment của Django)
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
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
    path('van-ban-den/them/', views.van_ban_den_them, name='vbd_them'),
    path('van-ban-den/<int:pk>/xem/', views.van_ban_den_xem, name='vbd_xem'),
    path('van-ban-den/<int:pk>/sua/', views.van_ban_den_sua, name='vbd_sua'),
    path('van-ban-den/<int:pk>/xoa/', views.van_ban_den_xoa, name='vbd_xoa'),
    path('van-ban-den/lich-su/', views.van_ban_den_lich_su, name='vbd_lich_su'),

    # --- Văn bản đi ---
    path('van-ban-di/', views.van_ban_di_index, name='vbdi_index'),
    path('api/van-ban-di/them-moi/', views.api_vbdi_them_moi, name='api_vbdi_them_moi'),
    path('api/van-ban-di/<int:pk>/chi-tiet/', views.api_vbdi_chi_tiet, name='api_vbdi_chi_tiet'),
    path('api/van-ban-di/<int:pk>/cap-nhat/', views.api_vbdi_cap_nhat, name='api_vbdi_cap_nhat'),
    path('api/van-ban-di/<int:pk>/xoa/', views.api_vbdi_xoa, name='api_vbdi_xoa'),
    path('api/van-ban-di/<int:pk>/phe-duyet/', views.api_vbdi_phe_duyet, name='api_vbdi_phe_duyet'),
    path('api/van-ban-di/<int:pk>/phat-hanh/', views.api_vbdi_phat_hanh, name='api_vbdi_phat_hanh'),
    path('api/van-ban-di/<int:pk>/lich-su/', views.api_vbdi_lich_su, name='api_vbdi_lich_su'),

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
    path('api/nguoi-dung/update-status/', views.api_nguoi_dung_update_status, name='api_user_update_status'),
    path('api/vai-tro/list/', views.api_vai_tro_list, name='api_role_list'),

    # --- Xử lý văn bản ---
    path('xu-ly-van-ban/', views.xu_ly_van_ban_index, name='xlvb_index'),
    path('xu-ly-van-ban/bao-cao/', views.xu_ly_van_ban_bao_cao, name='xlvb_bao_cao'),
    path('xu-ly-van-ban/cap-nhat/', views.xu_ly_van_ban_cap_nhat, name='xlvb_cap_nhat'),
    path('xu-ly-van-ban/chuyen-tiep/', views.xu_ly_van_ban_chuyen_tiep, name='xlvb_chuyen_tiep'),
    path('xu-ly-van-ban/phan-cong/', views.xu_ly_van_ban_phan_cong, name='xlvb_phan_cong'),
    # API Xử lý văn bản
    path('api/xu-ly-van-ban/phan-cong/', views.api_phan_cong_xlvb, name='api_phan_cong_xlvb'),
    path('api/xu-ly-van-ban/cap-nhat/', views.api_cap_nhat_xlvb, name='api_cap_nhat_xlvb'),
    path('api/xu-ly-van-ban/chuyen-tiep/', views.api_chuyen_tiep_xlvb, name='api_chuyen_tiep_xlvb'),
    path('api/xu-ly-van-ban/bao-cao/', views.api_bao_cao_xlvb, name='api_bao_cao_xlvb'),
    path('quen-mat-khau/', views.quen_mat_khau_view, name='quen_mat_khau'),
    path('api/send-otp/', views.api_send_otp, name='api_send_otp'),
    path('api/reset-password/', views.api_confirm_reset, name='api_confirm_reset'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

