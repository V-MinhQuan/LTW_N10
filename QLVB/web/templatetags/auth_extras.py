from django import template

register = template.Library()

@register.filter(name='has_permission')
def has_permission(user, action):
    if not user.is_authenticated:
        return False
    # Giám đốc toàn quyền
    if user.is_giam_doc():
        return True
    
    # Kiểm tra theo logic can_perform_action trong model
    return user.can_perform_action(action)

@register.simple_tag
def can_approve(user):
    return user.is_authenticated and user.can_approve()

@register.simple_tag
def can_publish(user):
    return user.is_authenticated and user.can_publish()

@register.simple_tag
def can_manage_users(user):
    return user.is_authenticated and user.can_manage_users_and_units()

@register.simple_tag
def check_perm(user, action, obj=None):
    if not user or not user.is_authenticated:
        return False
    return user.can_perform_action(action, obj)
