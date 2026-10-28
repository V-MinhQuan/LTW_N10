with open('QLVB/web/models.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """    @property
    def van_ban(self):
        return self.VanBanDenID if self.VanBanDenID_id else self.VanBanDiID

    @property
    def trich_yeu(self):
        vb = self.van_ban
        return vb.TrichYeu if vb else ""

    @property
    def so_ky_hieu(self):
        vb = self.van_ban
        return vb.SoKyHieu if vb else ""\
"""

replacement = """    @property
    def van_ban(self):
        return self.VanBanDenID if self.VanBanDenID_id else self.VanBanDiID

    @property
    def trich_yeu(self):
        if hasattr(self, '_trich_yeu') and self._trich_yeu is not None:
            return self._trich_yeu
        vb = self.van_ban
        return vb.TrichYeu if vb else ""

    @trich_yeu.setter
    def trich_yeu(self, value):
        self._trich_yeu = value

    @property
    def so_ky_hieu(self):
        if hasattr(self, '_so_ky_hieu') and self._so_ky_hieu is not None:
            return self._so_ky_hieu
        vb = self.van_ban
        return vb.SoKyHieu if vb else ""

    @so_ky_hieu.setter
    def so_ky_hieu(self, value):
        self._so_ky_hieu = value\
"""

content_norm = content.replace('\r\n', '\n')
target_norm = target.replace('\r\n', '\n')
replacement_norm = replacement.replace('\r\n', '\n')

if target_norm in content_norm:
    content_norm = content_norm.replace(target_norm, replacement_norm, 1)
    with open('QLVB/web/models.py', 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(content_norm)
    print('SUCCESS: Updated models.py')
else:
    print('FAILED: target_norm not found')

