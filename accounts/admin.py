from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_is_blocked')

    def get_is_blocked(self, instance):
        # Fallback if profile doesn't exist yet for some reason
        if hasattr(instance, 'profile'):
            return instance.profile.is_blocked
        return False
    get_is_blocked.boolean = True
    get_is_blocked.short_description = 'Blocked'

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
