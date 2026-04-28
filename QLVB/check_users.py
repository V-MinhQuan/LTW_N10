from web.models import UserAccount

users = UserAccount.objects.all()
with open('user_status.txt', 'w', encoding='utf-8') as f:
    for u in users:
        f.write(f'{u.username} | is_active: {u.is_active} | TrangThai: {u.TrangThai} | trang_thai: {u.trang_thai}\n')
