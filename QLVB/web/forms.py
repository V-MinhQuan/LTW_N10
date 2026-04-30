from django import forms
from django.utils import timezone
from .models import VanBanDen, DonViBenNgoai, DonViBenTrong
from django.contrib.auth.forms import AuthenticationForm

class VanBanDenForm(forms.Form):
    so_ky_hieu = forms.CharField(max_length=50, required=True, error_messages={'required': 'Số ký hiệu là bắt buộc.'})
    trich_yeu = forms.CharField(max_length=255, required=True, error_messages={'required': 'Trích yếu là bắt buộc.'})
    loai_van_ban = forms.CharField(max_length=50, required=True, error_messages={'required': 'Loại văn bản là bắt buộc.'})
    ngay_ban_hanh = forms.DateField(required=True, error_messages={'required': 'Ngày ban hành là bắt buộc.'})
    ngay_nhan = forms.DateField(required=True, error_messages={'required': 'Ngày nhận là bắt buộc.'})
    don_vi_ngoai_id = forms.CharField(required=True, error_messages={'required': 'Đơn vị gửi là bắt buộc.'})
    don_vi_trong_id = forms.CharField(required=False)
    tep_dinh_kem = forms.FileField(required=False)
    xoa_tep_dinh_kem = forms.CharField(required=False)
    trang_thai = forms.CharField(max_length=50, required=False)
    
    def __init__(self, *args, **kwargs):
        self.instance_id = kwargs.pop('instance_id', None)
        super().__init__(*args, **kwargs)

    def clean_so_ky_hieu(self):
        so_ky_hieu = self.cleaned_data.get('so_ky_hieu')
        ngay_nhan = self.cleaned_data.get('ngay_nhan')
        
        if not so_ky_hieu or not ngay_nhan:
            return so_ky_hieu

        # Kiểm tra tính duy nhất trong cùng năm của Ngày nhận
        year = ngay_nhan.year
        query = VanBanDen.objects.filter(SoKyHieu=so_ky_hieu, NgayNhan__year=year)
        
        if self.instance_id:
            query = query.exclude(VanBanDenID=self.instance_id)
            
        if query.exists():
            raise forms.ValidationError(f"Số ký hiệu '{so_ky_hieu}' đã tồn tại trong năm {year}.")
        return so_ky_hieu

    def clean(self):
        cleaned_data = super().clean()
        ngay_ban_hanh = cleaned_data.get('ngay_ban_hanh')
        ngay_nhan = cleaned_data.get('ngay_nhan')
        tep_dinh_kem = cleaned_data.get('tep_dinh_kem')
        xoa_tep_dinh_kem = cleaned_data.get('xoa_tep_dinh_kem')

        # 1. Kiểm tra Ngày ban hành <= Ngày nhận
        if ngay_ban_hanh and ngay_nhan:
            if ngay_ban_hanh > ngay_nhan:
                self.add_error('ngay_ban_hanh', "Ngày ban hành không được lớn hơn ngày nhận.")

        # 2. Kiểm tra Ngày nhận <= Ngày hiện tại
        if ngay_nhan:
            if ngay_nhan > timezone.localdate():
                self.add_error('ngay_nhan', "Ngày nhận không được lớn hơn ngày hiện tại.")

        # 3. Kiểm tra phải có ít nhất một file đính kèm
        # Nếu thêm mới: phải có file trong tep_dinh_kem
        # Nếu sửa: 
        #   - Có file mới (tep_dinh_kem)
        #   - HOẶC có file cũ và không bị đánh dấu xóa (xoa_tep_dinh_kem != '1')
        
        has_file = False
        if tep_dinh_kem:
            has_file = True
        elif self.instance_id:
            instance = VanBanDen.objects.filter(pk=self.instance_id).first()
            if instance and instance.TepDinhKem and xoa_tep_dinh_kem != '1':
                has_file = True
        
        if not has_file:
            self.add_error('tep_dinh_kem', "Văn bản phải có ít nhất một file đính kèm.")

        return cleaned_data

    def clean_don_vi_ngoai_id(self):
        don_vi_id = self.cleaned_data.get('don_vi_ngoai_id', '')
        if not don_vi_id:
            dv = DonViBenNgoai.objects.first()
            if not dv:
                dv = DonViBenNgoai.objects.create(TenDonVi="Chưa xác định")
            return dv
        if str(don_vi_id).isdigit():
            dv = DonViBenNgoai.objects.filter(pk=don_vi_id).first()
            if dv: return dv
        dv, created = DonViBenNgoai.objects.get_or_create(TenDonVi=don_vi_id)
        return dv

    def clean_don_vi_trong_id(self):
        don_vi_id = self.cleaned_data.get('don_vi_trong_id', '')
        if not don_vi_id:
            return None
        if str(don_vi_id).isdigit():
            return DonViBenTrong.objects.filter(pk=don_vi_id).first()
        return DonViBenTrong.objects.filter(TenDonVi=don_vi_id).first()

    def save(self, user=None, instance=None):
        data = self.cleaned_data
        
        if instance:
            fields = ['so_ky_hieu', 'trich_yeu', 'loai_van_ban', 'ngay_ban_hanh', 'ngay_nhan', 'don_vi_ngoai_id', 'don_vi_trong_id', 'trang_thai']
            for field in fields:
                if field in data:
                    model_field = "".join(x.capitalize() for x in field.split('_'))
                    # Mapping manual cases
                    if field == 'so_ky_hieu': model_field = 'SoKyHieu'
                    if field == 'loai_van_ban': model_field = 'LoaiVanBan'
                    if field == 'trich_yeu': model_field = 'TrichYeu'
                    if field == 'trang_thai': model_field = 'TrangThai'
                    if field == 'don_vi_ngoai_id': model_field = 'DonViNgoaiID'
                    if field == 'don_vi_trong_id': model_field = 'DonViTrongID'
                    
                    setattr(instance, model_field, data[field])
            
            # Handle files separately
            file_upload = self.files.get('tep_dinh_kem') or data.get('tep_dinh_kem')
            if file_upload:
                instance.TepDinhKem = file_upload
            elif data.get('xoa_tep_dinh_kem') == '1':
                if instance.TepDinhKem:
                    instance.TepDinhKem.delete(save=False)
                instance.TepDinhKem = None

            instance.save()
            return instance
        else:
            file_upload = self.files.get('tep_dinh_kem') or data.get('tep_dinh_kem')
            # Create new instance
            vbd = VanBanDen.objects.create(
                SoKyHieu=data.get('so_ky_hieu'),
                TrichYeu=data.get('trich_yeu'),
                LoaiVanBan=data.get('loai_van_ban'),
                NgayBanHanh=data.get('ngay_ban_hanh'),
                NgayNhan=data.get('ngay_nhan'),
                DonViNgoaiID=data.get('don_vi_ngoai_id'),
                DonViTrongID=data.get('don_vi_trong_id'),
                TepDinhKem=file_upload,
                TrangThai=data.get('trang_thai', 'DANG_XU_LY'),
                UserID=user
            )
            return vbd

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Tên đăng nhập'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control',
        'placeholder': 'Mật khẩu'
    }))