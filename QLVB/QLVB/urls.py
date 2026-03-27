"""
URL configuration for QLVB project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from web import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # Trang chủ & Login
    path('', views.login, name='login'),
    path('index/', views.index, name='index'),

    # Văn bản đến
    path('van-ban-den/', views.van_ban_den_index, name='vbd_index'),

    # Văn bản đi
    path('van-ban-di/', views.van_ban_di_index, name='vbdi_index'),

    # Người dùng
    path('quan-ly-nguoi-dung/', views.quan_ly_nguoi_dung_index, name='qlnd_index'),
    path('quan-ly-nguoi-dung/thong-tin/', views.thong_tin_nguoi_dung, name='thong_tin_nguoi_dung'),

    # Đơn vị
    path('quan-ly-don-vi/ben-ngoai/', views.quan_ly_don_vi_ben_ngoai, name='qldv_ngoai'),
    path('quan-ly-don-vi/ben-trong/', views.quan_ly_don_vi_ben_trong, name='qldv_trong'),

    # Xử lý văn bản
    path('xu-ly-van-ban/', views.xu_ly_van_ban_index, name='xlvb_index'),
    path('xu-ly-van-ban/bao-cao/', views.xu_ly_van_ban_bao_cao, name='xlvb_bao_cao'),
    path('xu-ly-van-ban/cap-nhat/', views.xu_ly_van_ban_cap_nhat, name='xlvb_cap_nhat'),
    path('xu-ly-van-ban/chuyen-tiep/', views.xu_ly_van_ban_chuyen_tiep, name='xlvb_chuyen_tiep'),
    path('xu-ly-van-ban/phan-cong/', views.xu_ly_van_ban_phan_cong, name='xlvb_phan_cong'),
]
