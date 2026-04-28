from django.contrib.auth.hashers import make_password
from web.models import UserAccount

users = UserAccount.objects.all()
count = 0
for u in users:
    if u.password == 'pbkdf2_sha256$123456' or len(u.password.split('$')) < 4:
        u.set_password('123456')
        u.save()
        count += 1
print(f'Updated {count} users')
